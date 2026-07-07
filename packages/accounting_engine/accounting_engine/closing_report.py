"""결산보고서(월간/연간) 렌더트리 빌더 — 재무 요약 + ML 파이프라인 산출물 결합."""
from .page import MARGIN_PT, new_page, title_node


def _fmt(n):
    if n is None:
        return "-"
    return f"{n:,.0f}"


def _fmt_pct(n):
    return "-" if n is None else f"{n:.2f}%"


def build_closing_report(
    company_name: str,
    period_label: str,
    bs_summary: dict,
    is_summary: dict,
    ratios: dict,
    ml_summary: dict,
    monthly_trend: dict,
) -> dict:
    kpi_rows = [
        ["자산총계", _fmt(bs_summary.get("asset_total"))],
        ["부채총계", _fmt(bs_summary.get("liability_total"))],
        ["자본총계", _fmt(bs_summary.get("equity_total"))],
        ["매출총계", _fmt(is_summary.get("revenue_total"))],
        ["비용총계", _fmt(is_summary.get("expense_total"))],
        ["당기순이익", _fmt(is_summary.get("net_income"))],
        ["부채비율", _fmt_pct(ratios.get("debt_ratio_pct"))],
        ["자기자본비율", _fmt_pct(ratios.get("equity_ratio_pct"))],
        ["순이익률", _fmt_pct(ratios.get("net_margin_pct"))],
    ]

    ml_rows = [
        ["이상거래 탐지 건수", str(ml_summary.get("anomaly_count", 0))],
        ["계정과목 자동분류 평균 신뢰도", _fmt_pct((ml_summary.get("avg_classification_confidence") or 0) * 100)],
        [
            f"{ml_summary.get('forecast_metric_label', '다음 기간 예측')}",
            _fmt(ml_summary.get("forecast_value")),
        ],
    ]

    page1_nodes = [
        title_node(f"{company_name} 결산보고서", y=730, font_size=18),
        {
            "type": "text", "x": MARGIN_PT, "y": 705, "w": 468, "h": 20,
            "style": {"font_key": "body", "font_size": 11},
            "text": f"대상기간: {period_label}",
        },
        {
            "type": "text", "x": MARGIN_PT, "y": 675, "w": 468, "h": 20,
            "style": {"font_key": "body", "font_size": 13},
            "text": "재무 요약",
        },
        {
            "type": "table", "x": MARGIN_PT, "y": 655,
            "col_widths": [234, 234], "row_height": 18,
            "rows": kpi_rows,
            "style": {"font_key": "body", "font_size": 10},
        },
        {
            "type": "text", "x": MARGIN_PT, "y": 655 - 18 * len(kpi_rows) - 25, "w": 468, "h": 20,
            "style": {"font_key": "body", "font_size": 13},
            "text": "AI/ML 분석 요약",
        },
        {
            "type": "table", "x": MARGIN_PT, "y": 655 - 18 * len(kpi_rows) - 45,
            "col_widths": [234, 234], "row_height": 18,
            "rows": ml_rows,
            "style": {"font_key": "body", "font_size": 10},
        },
    ]

    page2_nodes = [
        title_node("월별 추이 및 예측", y=730, font_size=16),
        {
            "type": "bar_chart",
            "x": MARGIN_PT, "y": 680, "w": 468, "h": 220,
            "categories": monthly_trend.get("categories", []),
            "values": monthly_trend.get("values", []),
            "title": monthly_trend.get("title", "월별 추이"),
            "style": {"font_key": "body"},
        },
    ]

    return {"render_tree": {"pages": [new_page(page1_nodes), new_page(page2_nodes)]}}
