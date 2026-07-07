"""
DART 표준계정 -> 내부 재무제표 요약/렌더트리 매퍼.
기업마다 IFRS 계정명 표기가 달라(예: '매출액' vs '영업수익') 후보 목록으로 매칭합니다.
"""
from accounting_engine.page import MARGIN_PT, new_page, title_node
from accounting_engine.ratios import compute_ratios

_ASSET_TOTAL = ["자산총계"]
_LIAB_TOTAL = ["부채총계"]
_EQUITY_TOTAL = ["자본총계"]
_REVENUE = ["매출액", "영업수익"]
_OPERATING_INCOME = ["영업이익"]
_NET_INCOME = ["당기순이익(손실)", "당기순이익"]


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _find_amount(items: list[dict], sj_div: str, candidates: list[str], field: str = "thstrm_amount"):
    for item in items:
        if item.get("sj_div") == sj_div and item.get("account_nm") in candidates:
            return _to_float(item.get(field))
    return None


def map_to_summary(items: list[dict]) -> dict:
    return {
        "asset_total": _find_amount(items, "BS", _ASSET_TOTAL),
        "liability_total": _find_amount(items, "BS", _LIAB_TOTAL),
        "equity_total": _find_amount(items, "BS", _EQUITY_TOTAL),
        "revenue_total": _find_amount(items, "IS", _REVENUE),
        "operating_income": _find_amount(items, "IS", _OPERATING_INCOME),
        "net_income": _find_amount(items, "IS", _NET_INCOME),
    }


def _fmt(n):
    return "-" if n is None else f"{n:,.0f}"


def build_dart_replica_render_tree(corp_name: str, bsns_year: str, items: list[dict], source: str) -> dict:
    summary = map_to_summary(items)
    ratios = compute_ratios(summary, summary)  # revenue_total/net_income 필드도 summary에 포함되어 있어 그대로 재사용

    def section_rows(sj_div):
        rows = []
        for item in items:
            if item.get("sj_div") != sj_div:
                continue
            rows.append([
                item.get("account_nm", ""),
                _fmt(_to_float(item.get("thstrm_amount"))),
                _fmt(_to_float(item.get("frmtrm_amount"))),
            ])
        return rows

    bs_rows = section_rows("BS")
    is_rows = section_rows("IS")

    page1_nodes = [
        title_node(f"{corp_name} — 공시 재무제표 재현 ({bsns_year})", y=730, font_size=16),
        {
            "type": "text", "x": MARGIN_PT, "y": 705, "w": 468, "h": 16,
            "style": {"font_key": "body", "font_size": 9},
            "text": f"출처: OpenDART ({'실시간 연동' if source == 'live' else '오프라인 fixture 데이터'})",
        },
        {
            "type": "table", "x": MARGIN_PT, "y": 680,
            "col_widths": [250, 109, 109], "row_height": 15,
            "header": ["재무상태표 계정", "당기금액", "전기금액"],
            "rows": bs_rows,
            "style": {"font_key": "body", "font_size": 8, "header_font_size": 8},
        },
    ]

    page2_nodes = [
        title_node("손익계산서 / 요약지표", y=730, font_size=16),
        {
            "type": "table", "x": MARGIN_PT, "y": 700,
            "col_widths": [250, 109, 109], "row_height": 15,
            "header": ["손익계산서 계정", "당기금액", "전기금액"],
            "rows": is_rows,
            "style": {"font_key": "body", "font_size": 8, "header_font_size": 8},
        },
        {
            "type": "table", "x": MARGIN_PT, "y": 700 - 15 * (len(is_rows) + 1) - 30,
            "col_widths": [234, 234], "row_height": 16,
            "header": ["재무비율", "값"],
            "rows": [
                ["부채비율", "-" if ratios["debt_ratio_pct"] is None else f"{ratios['debt_ratio_pct']:.2f}%"],
                ["자기자본비율", "-" if ratios["equity_ratio_pct"] is None else f"{ratios['equity_ratio_pct']:.2f}%"],
                ["순이익률", "-" if ratios["net_margin_pct"] is None else f"{ratios['net_margin_pct']:.2f}%"],
            ],
            "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
        },
    ]

    return {"summary": summary, "ratios": ratios, "render_tree": {"pages": [new_page(page1_nodes), new_page(page2_nodes)]}}
