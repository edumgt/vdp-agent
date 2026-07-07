from flask import Blueprint, jsonify, request
from shared import make_id

from ..db import query

bp = Blueprint("companies", __name__)


@bp.post("/api/companies")
def create_company():
    body = request.get_json(force=True) or {}
    name = body.get("name")
    biz_reg_no = body.get("biz_reg_no")
    if not name or not biz_reg_no:
        return jsonify({"error": "name, biz_reg_no는 필수입니다."}), 400

    company_id = make_id("CORP")
    query(
        "INSERT INTO companies(company_id, name, biz_reg_no, fiscal_year_end_month) VALUES (%s,%s,%s,%s)",
        [company_id, name, biz_reg_no, body.get("fiscal_year_end_month", 12)],
        fetch=None,
    )
    return jsonify({"company_id": company_id}), 201


@bp.get("/api/companies")
def list_companies():
    rows = query("SELECT * FROM companies ORDER BY created_at DESC")
    return jsonify(rows)


@bp.get("/api/companies/<company_id>")
def get_company(company_id):
    row = query("SELECT * FROM companies WHERE company_id=%s", [company_id], fetch="one")
    if not row:
        return jsonify({"error": "company not found"}), 404
    return jsonify(row)


@bp.get("/api/accounts")
def list_accounts():
    rows = query("SELECT * FROM accounts ORDER BY account_code")
    return jsonify(rows)
