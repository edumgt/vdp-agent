"""
재무비율 분석.
MVP는 유동/비유동 자산·부채 구분을 별도로 모델링하지 않으므로,
유동비율 등은 자산총계/부채총계 기준 근사치이며, 실제 재무분석 고도화 시
accounts에 유동성 분류(current/non_current) 필드를 추가해 정교화할 수 있습니다.
"""


def compute_ratios(bs_summary: dict, is_summary: dict) -> dict:
    assets = bs_summary.get("asset_total", 0) or 0
    liabilities = bs_summary.get("liability_total", 0) or 0
    equity = bs_summary.get("equity_total", 0) or 0
    revenue = is_summary.get("revenue_total", 0) or 0
    net_income = is_summary.get("net_income", 0) or 0

    return {
        "debt_ratio_pct": round((liabilities / equity) * 100, 2) if equity else None,
        "equity_ratio_pct": round((equity / assets) * 100, 2) if assets else None,
        "current_ratio_pct": round((assets / liabilities) * 100, 2) if liabilities else None,
        "net_margin_pct": round((net_income / revenue) * 100, 2) if revenue else None,
    }


def compute_export_ratio(tax_invoices: list[dict]) -> float | None:
    """매출 세금계산서 중 수출(export) 공급가액 비중(%). 매출 거래가 없으면 None."""
    sales = [inv for inv in tax_invoices if inv["direction"] == "sales"]
    total = sum(float(inv["supply_amount"]) for inv in sales)
    if not total:
        return None
    export_total = sum(float(inv["supply_amount"]) for inv in sales if inv.get("market") == "export")
    return round((export_total / total) * 100, 2)
