"""세금계산서(매입/매출) 정리표 빌더."""
from .page import MARGIN_PT, new_page, title_node


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _filter_by_date(invoices: list[dict], start=None, end=None) -> list[dict]:
    out = []
    for inv in invoices:
        d = str(inv["issue_date"])
        if start and d < str(start):
            continue
        if end and d > str(end):
            continue
        out.append(inv)
    return out


def compute_tax_summary(tax_invoices: list[dict], period_start=None, period_end=None) -> dict:
    filtered = _filter_by_date(tax_invoices, period_start, period_end)
    sales = [i for i in filtered if i["direction"] == "sales"]
    purchases = [i for i in filtered if i["direction"] == "purchase"]

    def totals(items):
        supply = sum(float(i["supply_amount"]) for i in items)
        tax = sum(float(i["tax_amount"]) for i in items)
        return supply, tax

    sales_supply, sales_tax = totals(sales)
    purchase_supply, purchase_tax = totals(purchases)

    return {
        "sales": sales, "purchases": purchases,
        "sales_supply": sales_supply, "sales_tax": sales_tax,
        "purchase_supply": purchase_supply, "purchase_tax": purchase_tax,
        "vat_payable": sales_tax - purchase_tax,
    }


def build_tax_summary(tax_invoices: list[dict], period_start=None, period_end=None) -> dict:
    summary = compute_tax_summary(tax_invoices, period_start, period_end)

    def section(items, label):
        rows = [[str(i["issue_date"]), i["counterparty_name"], _fmt(float(i["supply_amount"])), _fmt(float(i["tax_amount"]))] for i in items]
        return [["", f"[{label}]", "", ""]] + rows

    rows = (
        section(summary["sales"], "매출")
        + [["", "매출 합계", _fmt(summary["sales_supply"]), _fmt(summary["sales_tax"])]]
        + section(summary["purchases"], "매입")
        + [["", "매입 합계", _fmt(summary["purchase_supply"]), _fmt(summary["purchase_tax"])]]
        + [["", "납부(환급)세액", "", _fmt(summary["vat_payable"])]]
    )

    title = f"세금계산서/증빙 정리표 ({period_start or '~'} ~ {period_end or '~'})"
    nodes = [
        title_node(title, y=720, font_size=16),
        {
            "type": "table",
            "x": MARGIN_PT, "y": 680,
            "col_widths": [70, 218, 90, 90],
            "row_height": 16,
            "header": ["발행일자", "거래처", "공급가액", "세액"],
            "rows": rows,
            "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
        },
    ]

    return {"summary": summary, "render_tree": {"pages": [new_page(nodes)]}}
