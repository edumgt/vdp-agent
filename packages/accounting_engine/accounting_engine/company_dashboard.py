"""회사 대시보드: 재무비율 + 수출비중 요약 + 제조원가명세서 + 유형자산 목록을 하나의 보고서로 결합."""
from .fixed_assets import build_fixed_asset_list
from .manufacturing_cost import build_manufacturing_cost_statement
from .page import MARGIN_PT, new_page, title_node
from .ratios import compute_export_ratio, compute_ratios


def _fmt(n):
    return "-" if n is None else f"{n:,.0f}"


def _fmt_pct(n):
    return "-" if n is None else f"{n:.2f}%"


def build_company_dashboard(
    company_name: str,
    as_of_date: str,
    bs_summary: dict,
    is_summary: dict,
    tax_invoices: list[dict],
    accounts: list[dict],
    journal_lines: list[dict],
    fixed_assets: list[dict],
    period_start=None,
    period_end=None,
    beginning_wip: float = 0,
    ending_wip: float = 0,
) -> dict:
    ratios = compute_ratios(bs_summary, is_summary)
    export_ratio_pct = compute_export_ratio(tax_invoices)

    overview_rows = [
        ["자산총계", _fmt(bs_summary.get("asset_total"))],
        ["부채총계", _fmt(bs_summary.get("liability_total"))],
        ["자본총계", _fmt(bs_summary.get("equity_total"))],
        ["매출총계", _fmt(is_summary.get("revenue_total"))],
        ["당기순이익", _fmt(is_summary.get("net_income"))],
        ["부채비율", _fmt_pct(ratios.get("debt_ratio_pct"))],
        ["순이익률", _fmt_pct(ratios.get("net_margin_pct"))],
        ["수출비중(매출 세금계산서 기준)", _fmt_pct(export_ratio_pct)],
    ]

    page1_nodes = [
        title_node(f"{company_name} — 기업 대시보드", y=730, font_size=18),
        {
            "type": "text", "x": MARGIN_PT, "y": 705, "w": 468, "h": 16,
            "style": {"font_key": "body", "font_size": 10},
            "text": f"기준일: {as_of_date}",
        },
        {
            "type": "table", "x": MARGIN_PT, "y": 680,
            "col_widths": [234, 234], "row_height": 18,
            "rows": overview_rows,
            "style": {"font_key": "body", "font_size": 10},
        },
    ]

    manufacturing = build_manufacturing_cost_statement(accounts, journal_lines, period_start, period_end, beginning_wip, ending_wip)
    asset_list = build_fixed_asset_list(fixed_assets, as_of_date)

    pages = [new_page(page1_nodes)] + manufacturing["render_tree"]["pages"] + asset_list["render_tree"]["pages"]

    return {
        "summary": {
            "ratios": ratios,
            "export_ratio_pct": export_ratio_pct,
            "manufacturing": manufacturing["summary"],
            "fixed_assets": asset_list["summary"],
        },
        "render_tree": {"pages": pages},
    }
