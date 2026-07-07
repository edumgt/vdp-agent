"""유형자산 목록 + 정액법 감가상각 계산."""
import datetime

from .page import MARGIN_PT, new_page, title_node


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def compute_depreciation(asset: dict, as_of_date) -> dict:
    """정액법(straight-line) 감가상각. disposed_at이 있으면 그 시점까지만 상각."""
    as_of = _as_date(as_of_date)
    acquired = _as_date(asset["acquisition_date"])
    if asset.get("disposed_at"):
        as_of = min(as_of, _as_date(asset["disposed_at"]))

    cost = float(asset["acquisition_cost"])
    salvage = float(asset.get("salvage_value") or 0)
    useful_life = int(asset["useful_life_years"])

    elapsed_years = max(0.0, (as_of - acquired).days / 365.25)
    elapsed_years = min(elapsed_years, useful_life)

    depreciable_base = cost - salvage
    annual_depreciation = depreciable_base / useful_life if useful_life else 0.0
    accumulated_depreciation = min(annual_depreciation * elapsed_years, depreciable_base)
    book_value = cost - accumulated_depreciation

    return {
        "acquisition_cost": cost,
        "accumulated_depreciation": accumulated_depreciation,
        "book_value": book_value,
    }


def compute_fixed_asset_summary(fixed_assets: list[dict], as_of_date) -> dict:
    rows = []
    total_cost = 0.0
    total_accum = 0.0
    total_book = 0.0
    for asset in fixed_assets:
        dep = compute_depreciation(asset, as_of_date)
        rows.append({**asset, **dep})
        total_cost += dep["acquisition_cost"]
        total_accum += dep["accumulated_depreciation"]
        total_book += dep["book_value"]
    return {"assets": rows, "total_cost": total_cost, "total_accumulated_depreciation": total_accum, "total_book_value": total_book}


def build_fixed_asset_list(fixed_assets: list[dict], as_of_date) -> dict:
    summary = compute_fixed_asset_summary(fixed_assets, as_of_date)

    rows = [
        [a["name"], a["account_code"], str(a["acquisition_date"]), _fmt(a["acquisition_cost"]), _fmt(a["accumulated_depreciation"]), _fmt(a["book_value"])]
        for a in summary["assets"]
    ]
    rows.append(["합계", "", "", _fmt(summary["total_cost"]), _fmt(summary["total_accumulated_depreciation"]), _fmt(summary["total_book_value"])])

    nodes = [
        title_node(f"유형자산 목록 (기준일: {as_of_date})", y=720, font_size=16),
        {
            "type": "table", "x": MARGIN_PT, "y": 680,
            "col_widths": [140, 50, 70, 78, 78, 52], "row_height": 16,
            "header": ["자산명", "계정", "취득일", "취득원가", "상각누계액", "장부가액"],
            "rows": rows,
            "style": {"font_key": "body", "font_size": 8, "header_font_size": 8},
        },
    ]

    return {"summary": summary, "render_tree": {"pages": [new_page(nodes)]}}
