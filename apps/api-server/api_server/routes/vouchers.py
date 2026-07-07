import os

from flask import Blueprint, jsonify, request
from shared import make_id

from ..db import query
from ..queue import job_queue

bp = Blueprint("vouchers", __name__)


def _upload_dir():
    d = os.path.abspath(os.environ.get("LOCAL_UPLOAD_DIR", "./storage/uploads"))
    os.makedirs(d, exist_ok=True)
    return d


@bp.post("/api/vouchers")
def upload_voucher():
    company_id = request.form.get("company_id")
    voucher_type = request.form.get("voucher_type")
    file = request.files.get("file")

    if not company_id or not voucher_type or not file:
        return jsonify({"error": "company_id, voucher_type, file은 필수입니다."}), 400
    if voucher_type not in ("receipt", "tax_invoice"):
        return jsonify({"error": "voucher_type은 receipt 또는 tax_invoice여야 합니다."}), 400

    voucher_id = make_id("VCH")
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    file_path = os.path.join(_upload_dir(), f"{voucher_id}{ext}")
    file.save(file_path)

    query(
        "INSERT INTO vouchers(voucher_id, company_id, voucher_type, file_path, status) VALUES (%s,%s,%s,%s,'uploaded')",
        [voucher_id, company_id, voucher_type, file_path],
        fetch=None,
    )

    job_queue.enqueue("worker_jobs.jobs.ocr_voucher", voucher_id)

    return jsonify({"voucher_id": voucher_id, "status": "uploaded"}), 201


@bp.get("/api/vouchers")
def list_vouchers():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id 쿼리 파라미터가 필요합니다."}), 400
    rows = query("SELECT * FROM vouchers WHERE company_id=%s ORDER BY created_at DESC", [company_id])
    return jsonify(rows)


@bp.get("/api/vouchers/<voucher_id>")
def get_voucher(voucher_id):
    row = query("SELECT * FROM vouchers WHERE voucher_id=%s", [voucher_id], fetch="one")
    if not row:
        return jsonify({"error": "voucher not found"}), 404
    return jsonify(row)
