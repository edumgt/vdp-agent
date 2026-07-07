import os
from datetime import date

from flask import Blueprint, jsonify, request, send_file
from shared import make_id

from accounting_data import fetch_accounts, fetch_company, fetch_fixed_assets, fetch_journal_lines, fetch_tax_invoices, get_conn
from accounting_engine import build_company_dashboard, compute_statement_summary

from ..db import query
from ..queue import job_queue

bp = Blueprint("reports", __name__)

_REPORT_TYPES = {"financial_statement", "ledger", "tax_summary", "closing_report", "company_dashboard"}


@bp.post("/api/reports/generate")
def generate_report():
    body = request.get_json(force=True) or {}
    company_id = body.get("company_id")
    report_type = body.get("report_type")

    if not company_id or report_type not in _REPORT_TYPES:
        return jsonify({"error": f"company_id는 필수이며 report_type은 {sorted(_REPORT_TYPES)} 중 하나여야 합니다."}), 400

    report_id = make_id("RPT")
    query(
        "INSERT INTO pdf_reports(report_id, company_id, report_type, period_start, period_end, status) VALUES (%s,%s,%s,%s,%s,'pending')",
        [report_id, company_id, report_type, body.get("period_start"), body.get("period_end")],
        fetch=None,
    )

    job_queue.enqueue(
        "worker_jobs.jobs.generate_report",
        report_id,
        {
            "as_of_date": body.get("as_of_date"),
            "beginning_wip": body.get("beginning_wip", 0),
            "ending_wip": body.get("ending_wip", 0),
        },
    )

    return jsonify({"report_id": report_id, "status": "pending"}), 201


@bp.get("/api/reports/<report_id>")
def get_report(report_id):
    row = query("SELECT * FROM pdf_reports WHERE report_id=%s", [report_id], fetch="one")
    if not row:
        return jsonify({"error": "report not found"}), 404
    return jsonify(row)


@bp.get("/api/reports/<report_id>/pdf")
def download_report(report_id):
    row = query("SELECT * FROM pdf_reports WHERE report_id=%s", [report_id], fetch="one")
    if not row:
        return jsonify({"error": "report not found"}), 404
    if row["status"] != "done" or not row["file_path"] or not os.path.exists(row["file_path"]):
        return jsonify({"error": "report not ready", "status": row["status"]}), 409
    return send_file(row["file_path"], mimetype="application/pdf", as_attachment=True, download_name=f"{report_id}.pdf")


@bp.get("/api/companies/<company_id>/dashboard")
def company_dashboard(company_id):
    """PDF 없이 즉시 계산되는 웹 대시보드용 JSON (재무요약/수출비중/제조원가/유형자산)."""
    as_of_date = request.args.get("as_of_date") or date.today().isoformat()
    period_start = request.args.get("period_start")
    period_end = request.args.get("period_end")

    conn = get_conn()
    try:
        company = fetch_company(conn, company_id)
        if not company:
            return jsonify({"error": "company not found"}), 404
        accounts = fetch_accounts(conn)
        journal_lines = fetch_journal_lines(conn, company_id, period_start, period_end)
        tax_invoices = fetch_tax_invoices(conn, company_id, period_start, period_end)
        fixed_assets = fetch_fixed_assets(conn, company_id)
    finally:
        conn.close()

    bs_summary_full = compute_statement_summary(accounts, journal_lines)
    bs_summary = {
        "asset_total": bs_summary_full["by_type"]["asset"],
        "liability_total": bs_summary_full["by_type"]["liability"],
        "equity_total": bs_summary_full["by_type"]["equity"],
    }
    is_summary = {
        "revenue_total": bs_summary_full["by_type"]["revenue"],
        "expense_total": bs_summary_full["by_type"]["expense"],
        "net_income": bs_summary_full["by_type"]["revenue"] - bs_summary_full["by_type"]["expense"],
    }

    result = build_company_dashboard(
        company_name=company["name"],
        as_of_date=as_of_date or "전체 기간",
        bs_summary=bs_summary,
        is_summary=is_summary,
        tax_invoices=tax_invoices,
        accounts=accounts,
        journal_lines=journal_lines,
        fixed_assets=fixed_assets,
        period_start=period_start,
        period_end=period_end,
    )

    return jsonify({
        "company": company,
        "financials": {**bs_summary, **is_summary},
        "ratios": result["summary"]["ratios"],
        "export_ratio_pct": result["summary"]["export_ratio_pct"],
        "manufacturing": result["summary"]["manufacturing"],
        "fixed_assets": result["summary"]["fixed_assets"],
    })
