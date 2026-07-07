from flask import Blueprint, jsonify, request
from shared import make_id

from ..db import query
from ..queue import job_queue

bp = Blueprint("journal", __name__)


@bp.post("/api/journal-entries")
def create_journal_entry():
    body = request.get_json(force=True) or {}
    company_id = body.get("company_id")
    entry_date = body.get("entry_date")
    description = body.get("description")
    lines = body.get("lines") or []
    source_type = body.get("source_type", "manual")

    if not company_id or not entry_date or not description or not lines:
        return jsonify({"error": "company_id, entry_date, description, lines는 필수입니다."}), 400

    debit_sum = sum(float(line.get("debit") or 0) for line in lines)
    credit_sum = sum(float(line.get("credit") or 0) for line in lines)
    if abs(debit_sum - credit_sum) > 0.01:
        return jsonify({"error": f"차변({debit_sum})과 대변({credit_sum})의 합이 일치하지 않습니다."}), 400

    entry_id = make_id("JE")
    conn_sql = "INSERT INTO journal_entries(entry_id, company_id, entry_date, description, source_type, voucher_id) VALUES (%s,%s,%s,%s,%s,%s)"
    query(conn_sql, [entry_id, company_id, entry_date, description, source_type, body.get("voucher_id")], fetch=None)

    for line in lines:
        query(
            "INSERT INTO journal_lines(entry_id, account_code, debit, credit, memo) VALUES (%s,%s,%s,%s,%s)",
            [entry_id, line["account_code"], line.get("debit", 0), line.get("credit", 0), line.get("memo")],
            fetch=None,
        )

    if len(lines) == 2:
        job_queue.enqueue("worker_jobs.jobs.classify_entry", entry_id)

    return jsonify({"entry_id": entry_id}), 201


@bp.get("/api/journal-entries")
def list_journal_entries():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id 쿼리 파라미터가 필요합니다."}), 400
    rows = query(
        "SELECT * FROM journal_entries WHERE company_id=%s ORDER BY entry_date DESC, entry_id DESC",
        [company_id],
    )
    return jsonify(rows)


@bp.get("/api/journal-entries/<entry_id>")
def get_journal_entry(entry_id):
    entry = query("SELECT * FROM journal_entries WHERE entry_id=%s", [entry_id], fetch="one")
    if not entry:
        return jsonify({"error": "entry not found"}), 404
    lines = query("SELECT * FROM journal_lines WHERE entry_id=%s", [entry_id])
    classification = query(
        "SELECT * FROM ml_classifications WHERE entry_id=%s ORDER BY created_at DESC LIMIT 1", [entry_id], fetch="one"
    )
    return jsonify({"entry": entry, "lines": lines, "ml_classification": classification})
