#!/usr/bin/env python3
"""
Flask/RQ 없이 패키지를 직접 호출해 5종 보고서를 한번에 생성하는 데모/스모크 테스트 스크립트.
사전 조건: python scripts/db_migrate.py && python scripts/db_seed.py, assets/fonts에 폰트 배치.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db_util import get_conn  # noqa: E402

from accounting_data import fetch_accounts, fetch_fixed_assets, fetch_journal_lines, fetch_tax_invoices, query  # noqa: E402
from accounting_engine import (  # noqa: E402
    build_closing_report,
    build_company_dashboard,
    build_financial_statement_report,
    build_general_ledger,
    build_journal_register,
    build_tax_summary,
    compute_ratios,
    compute_statement_summary,
)
from ml_pipeline import detect_anomalies  # noqa: E402
from ml_pipeline.forecast import forecast_metric, monthly_series  # noqa: E402
from pdf_engine import render_pdf  # noqa: E402

COMPANY_ID = "CORP-0001"
PERIOD_START, PERIOD_END = "2026-01-01", "2026-06-30"
OUT_DIR = Path(__file__).resolve().parent.parent / "storage" / "pdfs"
FONT_MAP = {"body": "NotoSansKR-Regular.ttf"}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    try:
        accounts = fetch_accounts(conn)
        journal_lines = fetch_journal_lines(conn, COMPANY_ID, PERIOD_START, PERIOD_END)
        tax_invoices = fetch_tax_invoices(conn, COMPANY_ID, PERIOD_START, PERIOD_END)
        fixed_assets = fetch_fixed_assets(conn, COMPANY_ID)
        company = query(conn, "SELECT * FROM companies WHERE company_id=%s", [COMPANY_ID], fetch="one")
    finally:
        conn.close()

    reports = {}

    fs = build_financial_statement_report(accounts, journal_lines, PERIOD_END, PERIOD_START, PERIOD_END)
    reports["financial_statement"] = fs["render_tree"]

    reports["ledger"] = {
        "pages": build_journal_register(journal_lines, accounts)["pages"] + build_general_ledger(accounts, journal_lines)["pages"]
    }

    reports["tax_summary"] = build_tax_summary(tax_invoices, PERIOD_START, PERIOD_END)["render_tree"]

    by_type = compute_statement_summary(accounts, journal_lines)["by_type"]
    bs_summary = {"asset_total": by_type["asset"], "liability_total": by_type["liability"], "equity_total": by_type["equity"]}
    is_summary = {"revenue_total": by_type["revenue"], "expense_total": by_type["expense"], "net_income": by_type["revenue"] - by_type["expense"]}
    ratios = compute_ratios(bs_summary, is_summary)
    anomalies = detect_anomalies(journal_lines)
    series = monthly_series(journal_lines, lambda line: (float(line["credit"]) - float(line["debit"])) if line["account_code"] in ("401", "411") else 0.0)
    values = [v for _, v in series]
    forecast_value = forecast_metric(values, 1)["forecast"][0] if len(values) >= 2 else None
    reports["closing_report"] = build_closing_report(
        company_name=company["name"], period_label=f"{PERIOD_START} ~ {PERIOD_END}",
        bs_summary=bs_summary, is_summary=is_summary, ratios=ratios,
        ml_summary={"anomaly_count": len(anomalies), "avg_classification_confidence": 0.0,
                    "forecast_metric_label": "다음달 매출 예측", "forecast_value": forecast_value},
        monthly_trend={"categories": [p for p, _ in series], "values": values, "title": "월별 매출 추이"},
    )["render_tree"]

    reports["company_dashboard"] = build_company_dashboard(
        company_name=company["name"], as_of_date=PERIOD_END, bs_summary=bs_summary, is_summary=is_summary,
        tax_invoices=tax_invoices, accounts=accounts, journal_lines=journal_lines, fixed_assets=fixed_assets,
        period_start=PERIOD_START, period_end=PERIOD_END,
    )["render_tree"]

    for name, render_tree in reports.items():
        out_path = OUT_DIR / f"demo_{name}.pdf"
        result = render_pdf(render_tree, FONT_MAP, str(out_path))
        print(f"[demo] {name}: {out_path} ({result['pages']} pages, {result['size']} bytes)")


if __name__ == "__main__":
    main()
