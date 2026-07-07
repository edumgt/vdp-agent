from flask import Blueprint, jsonify, request

from accounting_data import fetch_journal_lines, get_conn
from ml_pipeline import AccountClassifier, detect_anomalies
from ml_pipeline.forecast import forecast_metric, monthly_series

from ..db import query

bp = Blueprint("ml", __name__)

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = AccountClassifier.load_default()
    return _classifier


@bp.post("/api/ml/classify-preview")
def classify_preview():
    body = request.get_json(force=True) or {}
    text = body.get("description") or body.get("text")
    if not text:
        return jsonify({"error": "description(거래 적요 텍스트)가 필요합니다."}), 400
    return jsonify(_get_classifier().predict(text))


@bp.get("/api/ml/anomalies")
def get_anomalies():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id 쿼리 파라미터가 필요합니다."}), 400

    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_conn()
    try:
        lines = fetch_journal_lines(conn, company_id, start, end)
    finally:
        conn.close()

    anomalies = detect_anomalies(lines)

    for a in anomalies:
        query(
            "INSERT INTO ml_anomalies(entry_id, score, reason, model_version) VALUES (%s,%s,%s,%s)",
            [a["entry_id"], a["score"], a["reason"], a["model_version"]],
            fetch=None,
        )

    return jsonify(anomalies)


@bp.get("/api/ml/forecast")
def get_forecast():
    company_id = request.args.get("company_id")
    metric = request.args.get("metric", "revenue")
    periods_ahead = int(request.args.get("periods_ahead", 3))
    if not company_id or metric not in ("cash_flow", "revenue"):
        return jsonify({"error": "company_id는 필수이며 metric은 cash_flow 또는 revenue여야 합니다."}), 400

    conn = get_conn()
    try:
        lines = fetch_journal_lines(conn, company_id)
    finally:
        conn.close()

    if metric == "revenue":
        revenue_codes = {"401", "411"}

        def value_fn(line):
            return (float(line["credit"]) - float(line["debit"])) if line["account_code"] in revenue_codes else 0.0
    else:
        cash_codes = {"101", "102"}

        def value_fn(line):
            return (float(line["debit"]) - float(line["credit"])) if line["account_code"] in cash_codes else 0.0

    series = monthly_series(lines, value_fn)
    values = [v for _, v in series]

    try:
        result = forecast_metric(values, periods_ahead)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    for i, forecast_value in enumerate(result["forecast"]):
        query(
            "INSERT INTO ml_forecasts(company_id, metric, period, predicted_value, model_version) VALUES (%s,%s,%s,%s,%s)",
            [company_id, metric, f"+{i + 1}", forecast_value, result["model_version"]],
            fetch=None,
        )

    return jsonify({"history": series, "forecast": result["forecast"], "model_version": result["model_version"]})
