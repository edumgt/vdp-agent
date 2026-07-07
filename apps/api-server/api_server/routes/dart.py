from flask import Blueprint, jsonify, request
from shared import make_id

from dart_integration import search_corp_code

from ..db import query
from ..queue import job_queue

bp = Blueprint("dart", __name__)


@bp.get("/api/dart/search")
def dart_search():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "name 쿼리 파라미터가 필요합니다."}), 400
    result = search_corp_code(name)
    return jsonify(result)


@bp.post("/api/dart/companies/<corp_code>/regenerate")
def dart_regenerate(corp_code):
    body = request.get_json(force=True) or {}
    company_id = body.get("company_id")
    corp_name = body.get("corp_name", corp_code)
    bsns_year = body.get("bsns_year")
    if not company_id or not bsns_year:
        return jsonify({"error": "company_id, bsns_year는 필수입니다."}), 400

    report_id = make_id("RPT")
    query(
        "INSERT INTO pdf_reports(report_id, company_id, report_type, status) VALUES (%s,%s,'dart_replica','pending')",
        [report_id, company_id],
        fetch=None,
    )

    job_queue.enqueue("worker_jobs.jobs.dart_regenerate", report_id, corp_code, corp_name, bsns_year)

    return jsonify({"report_id": report_id, "status": "pending"}), 201
