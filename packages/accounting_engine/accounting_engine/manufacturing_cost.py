"""
제조원가명세서(Statement of Cost of Goods Manufactured) 빌더.
accounts.cost_category(material/labor/overhead)로 태깅된 비용 계정만 집계 대상이 됩니다.
기초/기말 재공품(WIP)은 별도 재고자산 실사 프로세스가 필요해 MVP에서는 호출 시 값을 입력받습니다.
"""
from .accounts import sum_lines_by_account
from .page import MARGIN_PT, new_page, title_node

_CATEGORY_LABELS = {"material": "재료비", "labor": "노무비", "overhead": "제조경비"}


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _filter_by_date(journal_lines: list[dict], start=None, end=None) -> list[dict]:
    out = []
    for line in journal_lines:
        d = str(line["entry_date"])
        if start and d < str(start):
            continue
        if end and d > str(end):
            continue
        out.append(line)
    return out


def compute_manufacturing_cost_summary(
    accounts: list[dict], journal_lines: list[dict], period_start=None, period_end=None,
    beginning_wip: float = 0, ending_wip: float = 0,
) -> dict:
    filtered = _filter_by_date(journal_lines, period_start, period_end)
    totals = sum_lines_by_account(filtered)
    cost_by_category = {"material": 0.0, "labor": 0.0, "overhead": 0.0}
    detail_by_category = {"material": [], "labor": [], "overhead": []}

    for account in accounts:
        category = account.get("cost_category")
        if category not in cost_by_category:
            continue
        bucket = totals.get(account["account_code"], {"debit": 0.0, "credit": 0.0})
        amount = bucket["debit"] - bucket["credit"]
        if amount == 0:
            continue
        cost_by_category[category] += amount
        detail_by_category[category].append((account, amount))

    total_manufacturing_cost = sum(cost_by_category.values())
    cost_of_goods_manufactured = beginning_wip + total_manufacturing_cost - ending_wip

    return {
        "cost_by_category": cost_by_category,
        "detail_by_category": detail_by_category,
        "total_manufacturing_cost": total_manufacturing_cost,
        "beginning_wip": beginning_wip,
        "ending_wip": ending_wip,
        "cost_of_goods_manufactured": cost_of_goods_manufactured,
    }


def build_manufacturing_cost_statement(
    accounts: list[dict], journal_lines: list[dict], period_start=None, period_end=None,
    beginning_wip: float = 0, ending_wip: float = 0,
) -> dict:
    summary = compute_manufacturing_cost_summary(accounts, journal_lines, period_start, period_end, beginning_wip, ending_wip)

    rows = []
    for category in ("material", "labor", "overhead"):
        rows.append(["", f"[{_CATEGORY_LABELS[category]}]", ""])
        for account, amount in summary["detail_by_category"][category]:
            rows.append([account["account_code"], account["name"], _fmt(amount)])
        rows.append(["", f"{_CATEGORY_LABELS[category]} 소계", _fmt(summary["cost_by_category"][category])])

    rows += [
        ["", "당기총제조비용", _fmt(summary["total_manufacturing_cost"])],
        ["", "기초재공품재고액", _fmt(summary["beginning_wip"])],
        ["", "기말재공품재고액", _fmt(summary["ending_wip"])],
        ["", "당기제품제조원가", _fmt(summary["cost_of_goods_manufactured"])],
    ]

    title = f"제조원가명세서 ({period_start or '~'} ~ {period_end or '~'})"
    nodes = [
        title_node(title, y=720, font_size=16),
        {
            "type": "table", "x": MARGIN_PT, "y": 680,
            "col_widths": [50, 300, 118], "row_height": 16,
            "header": ["코드", "항목", "금액"],
            "rows": rows,
            "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
        },
    ]

    return {"summary": summary, "render_tree": {"pages": [new_page(nodes)]}}
