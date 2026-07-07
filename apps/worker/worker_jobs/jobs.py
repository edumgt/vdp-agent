import hashlib
import os
from datetime import datetime, timezone

import psycopg2.extras
from accounting_data import fetch_accounts, fetch_fixed_assets, fetch_journal_lines, fetch_tax_invoices, get_conn, query
from accounting_engine import (
    build_closing_report,
    build_company_dashboard,
    build_financial_statement_report,
    build_general_ledger,
    build_journal_register,
    build_tax_summary,
    compute_ratios,
    compute_statement_summary,
)
from dart_integration import build_dart_replica_render_tree, fetch_financial_statements
from ml_pipeline import AccountClassifier, detect_anomalies, extract_fields, get_provider
from ml_pipeline.forecast import forecast_metric, monthly_series
from pdf_engine import render_pdf

_classifier = None


def _env(name, fallback=None):
    return os.environ.get(name, fallback)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _font_map():
    return {"body": _env("FONT_FILE", "NotoSansKR-Regular.ttf")}


def _pdf_dir():
    d = os.path.abspath(_env("LOCAL_PDF_DIR", "./storage/pdfs"))
    os.makedirs(d, exist_ok=True)
    return d


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = AccountClassifier.load_default()
    return _classifier


# ---------------------------------------------------------------------------
# OCR


def ocr_voucher(voucher_id: str):
    conn = get_conn()
    try:
        voucher = query(conn, "SELECT * FROM vouchers WHERE voucher_id=%s", [voucher_id], fetch="one")
        if not voucher:
            raise ValueError(f"voucher not found: {voucher_id}")

        provider = get_provider()
        try:
            ocr_result = provider.extract_text(voucher["file_path"])
            fields = extract_fields(ocr_result["text"])
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vouchers SET ocr_raw_text=%s, ocr_confidence=%s, extracted_json=%s, status='ocr_done' WHERE voucher_id=%s",
                    (ocr_result["text"], ocr_result["confidence"], psycopg2.extras.Json(fields), voucher_id),
                )
            conn.commit()
            return {"voucher_id": voucher_id, "fields": fields}
        except Exception:
            with conn.cursor() as cur:
                cur.execute("UPDATE vouchers SET status='ocr_failed' WHERE voucher_id=%s", (voucher_id,))
            conn.commit()
            raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 계정과목 자동분류


def classify_entry(entry_id: str):
    conn = get_conn()
    try:
        entry = query(conn, "SELECT * FROM journal_entries WHERE entry_id=%s", [entry_id], fetch="one")
        if not entry:
            raise ValueError(f"entry not found: {entry_id}")
        lines = query(conn, "SELECT * FROM journal_lines WHERE entry_id=%s", [entry_id])

        prediction = _get_classifier().predict(entry["description"])

        # 현금/예금(101,102)이 아닌 라인을 "실제 계정"으로 간주(단순 2줄 분개 기준)
        actual_line = next((line for line in lines if line["account_code"] not in ("101", "102")), lines[0])
        is_override = prediction["account_code"] != actual_line["account_code"]

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ml_classifications(entry_id, predicted_account_code, confidence, model_version, is_override) VALUES (%s,%s,%s,%s,%s)",
                (entry_id, prediction["account_code"], prediction["confidence"], prediction["model_version"], is_override),
            )
        conn.commit()
        return {"entry_id": entry_id, "prediction": prediction, "is_override": is_override}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PDF 보고서 생성


def _mark_report(conn, report_id, **fields):
    sets = ", ".join(f"{k}=%s" for k in fields)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE pdf_reports SET {sets} WHERE report_id=%s", [*fields.values(), report_id])
    conn.commit()


def _build_render_tree(conn, report, options):
    company_id = report["company_id"]
    report_type = report["report_type"]
    period_start = report["period_start"]
    period_end = report["period_end"]

    accounts = fetch_accounts(conn)
    journal_lines = fetch_journal_lines(conn, company_id, period_start, period_end)

    if report_type == "financial_statement":
        as_of = options.get("as_of_date") or period_end
        result = build_financial_statement_report(accounts, journal_lines, as_of, period_start, period_end)
        return result["render_tree"]

    if report_type == "ledger":
        register = build_journal_register(journal_lines, accounts)
        ledger = build_general_ledger(accounts, journal_lines)
        return {"pages": register["pages"] + ledger["pages"]}

    if report_type == "tax_summary":
        tax_invoices = fetch_tax_invoices(conn, company_id, period_start, period_end)
        return build_tax_summary(tax_invoices, period_start, period_end)["render_tree"]

    if report_type == "closing_report":
        stmt_summary = compute_statement_summary(accounts, journal_lines)
        bs_summary = {
            "asset_total": stmt_summary["by_type"]["asset"],
            "liability_total": stmt_summary["by_type"]["liability"],
            "equity_total": stmt_summary["by_type"]["equity"],
        }
        is_summary = {
            "revenue_total": stmt_summary["by_type"]["revenue"],
            "expense_total": stmt_summary["by_type"]["expense"],
            "net_income": stmt_summary["by_type"]["revenue"] - stmt_summary["by_type"]["expense"],
        }
        ratios = compute_ratios(bs_summary, is_summary)

        anomalies = detect_anomalies(journal_lines)
        classifications = query(
            conn,
            "SELECT c.* FROM ml_classifications c JOIN journal_entries je ON je.entry_id=c.entry_id WHERE je.company_id=%s",
            [company_id],
        )
        avg_confidence = (sum(c["confidence"] for c in classifications) / len(classifications)) if classifications else 0.0

        revenue_codes = {"401", "411"}
        series = monthly_series(
            journal_lines,
            lambda line: (float(line["credit"]) - float(line["debit"])) if line["account_code"] in revenue_codes else 0.0,
        )
        values = [v for _, v in series]
        forecast_value = None
        if len(values) >= 2:
            forecast_value = forecast_metric(values, 1)["forecast"][0]

        return build_closing_report(
            company_name=report.get("company_name", company_id),
            period_label=f"{period_start or '~'} ~ {period_end or '~'}",
            bs_summary=bs_summary,
            is_summary=is_summary,
            ratios=ratios,
            ml_summary={
                "anomaly_count": len(anomalies),
                "avg_classification_confidence": avg_confidence,
                "forecast_metric_label": "다음달 매출 예측",
                "forecast_value": forecast_value,
            },
            monthly_trend={"categories": [p for p, _ in series], "values": values, "title": "월별 매출 추이"},
        )["render_tree"]

    if report_type == "company_dashboard":
        tax_invoices = fetch_tax_invoices(conn, company_id, period_start, period_end)
        fixed_assets = fetch_fixed_assets(conn, company_id)
        as_of = options.get("as_of_date") or period_end

        by_type = compute_statement_summary(accounts, journal_lines)["by_type"]
        bs_summary = {"asset_total": by_type["asset"], "liability_total": by_type["liability"], "equity_total": by_type["equity"]}
        is_summary = {"revenue_total": by_type["revenue"], "expense_total": by_type["expense"], "net_income": by_type["revenue"] - by_type["expense"]}

        return build_company_dashboard(
            company_name=report.get("company_name", company_id),
            as_of_date=as_of,
            bs_summary=bs_summary,
            is_summary=is_summary,
            tax_invoices=tax_invoices,
            accounts=accounts,
            journal_lines=journal_lines,
            fixed_assets=fixed_assets,
            period_start=period_start,
            period_end=period_end,
            beginning_wip=options.get("beginning_wip", 0),
            ending_wip=options.get("ending_wip", 0),
        )["render_tree"]

    raise ValueError(f"unknown report_type: {report_type}")


def generate_report(report_id: str, options: dict | None = None):
    options = options or {}
    conn = get_conn()
    try:
        _mark_report(conn, report_id, status="running", started_at=_now())
        report = query(conn, "SELECT * FROM pdf_reports WHERE report_id=%s", [report_id], fetch="one")
        company = query(conn, "SELECT * FROM companies WHERE company_id=%s", [report["company_id"]], fetch="one")
        report["company_name"] = company["name"] if company else report["company_id"]

        render_tree = _build_render_tree(conn, report, options)

        out_path = os.path.join(_pdf_dir(), f"{report_id}.pdf")
        result = render_pdf(render_tree, _font_map(), out_path)

        with open(out_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        _mark_report(
            conn, report_id,
            status="done", file_path=out_path, file_hash=file_hash,
            source_snapshot=psycopg2.extras.Json({"report_type": report["report_type"], "pages": result["pages"]}),
            finished_at=_now(),
        )
        return result
    except Exception as e:
        _mark_report(conn, report_id, status="failed", error_log=str(e), finished_at=_now())
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DART 재현


def dart_regenerate(report_id: str, corp_code: str, corp_name: str, bsns_year: str):
    conn = get_conn()
    try:
        _mark_report(conn, report_id, status="running", started_at=_now())

        fs_result = fetch_financial_statements(corp_code, bsns_year)
        replica = build_dart_replica_render_tree(corp_name, bsns_year, fs_result["items"], fs_result["source"])

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dart_filings_cache(corp_code, corp_name, bsns_year, raw_response, source) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (corp_code, bsns_year) DO UPDATE SET raw_response=EXCLUDED.raw_response, source=EXCLUDED.source, fetched_at=NOW()",
                (corp_code, corp_name, bsns_year, psycopg2.extras.Json(fs_result["items"]), fs_result["source"]),
            )
        conn.commit()

        out_path = os.path.join(_pdf_dir(), f"{report_id}.pdf")
        result = render_pdf(replica["render_tree"], _font_map(), out_path)

        with open(out_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        _mark_report(
            conn, report_id,
            status="done", file_path=out_path, file_hash=file_hash,
            source_snapshot=psycopg2.extras.Json({"corp_code": corp_code, "bsns_year": bsns_year, "source": fs_result["source"], "summary": replica["summary"]}),
            finished_at=_now(),
        )
        return result
    except Exception as e:
        _mark_report(conn, report_id, status="failed", error_log=str(e), finished_at=_now())
        raise
    finally:
        conn.close()
