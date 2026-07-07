"""재무상태표(BS) / 손익계산서(IS) 집계 및 렌더트리 빌더."""
from .accounts import TYPE_LABELS_KO, account_balance, sum_lines_by_account
from .page import MARGIN_PT, new_page, title_node

_BS_TYPES = ["asset", "liability", "equity"]
_IS_TYPES = ["revenue", "expense"]


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


def compute_statement_summary(accounts: list[dict], journal_lines: list[dict]) -> dict:
    """계정유형별 잔액 집계. 재무상태표/손익계산서 공용."""
    totals = sum_lines_by_account(journal_lines)
    by_account = {}
    by_type = {t: 0.0 for t in TYPE_LABELS_KO}

    for account in accounts:
        code = account["account_code"]
        bucket = totals.get(code, {"debit": 0.0, "credit": 0.0})
        balance = account_balance(account, bucket["debit"], bucket["credit"])
        if balance == 0 and code not in totals:
            continue
        by_account[code] = {"account": account, "balance": balance}
        by_type[account["account_type"]] += balance

    return {"by_account": by_account, "by_type": by_type}


def build_balance_sheet(accounts: list[dict], journal_lines: list[dict], as_of_date=None) -> dict:
    filtered = _filter_by_date(journal_lines, end=as_of_date)
    summary = compute_statement_summary(accounts, filtered)

    def section_rows(account_type):
        rows = []
        subtotal = 0.0
        for entry in summary["by_account"].values():
            if entry["account"]["account_type"] != account_type:
                continue
            rows.append([entry["account"]["account_code"], entry["account"]["name"], _fmt(entry["balance"])])
            subtotal += entry["balance"]
        return rows, subtotal

    asset_rows, asset_total = section_rows("asset")
    liab_rows, liab_total = section_rows("liability")
    equity_rows, equity_total = section_rows("equity")

    rows = (
        [["", "[자산]", ""]] + asset_rows + [["", "자산총계", _fmt(asset_total)]]
        + [["", "[부채]", ""]] + liab_rows + [["", "부채총계", _fmt(liab_total)]]
        + [["", "[자본]", ""]] + equity_rows + [["", "자본총계", _fmt(equity_total)]]
        + [["", "부채와자본총계", _fmt(liab_total + equity_total)]]
    )

    title = f"재무상태표 (기준일: {as_of_date or '전체'})"
    nodes = [
        title_node(title, y=720, font_size=16),
        {
            "type": "table",
            "x": MARGIN_PT, "y": 680,
            "col_widths": [50, 300, 118],
            "row_height": 16,
            "header": ["코드", "계정과목", "금액"],
            "rows": rows,
            "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
        },
    ]

    return {
        "summary": {
            "asset_total": asset_total, "liability_total": liab_total, "equity_total": equity_total,
        },
        "render_tree": {"pages": [new_page(nodes)]},
    }


def build_income_statement(accounts: list[dict], journal_lines: list[dict], period_start=None, period_end=None) -> dict:
    filtered = _filter_by_date(journal_lines, start=period_start, end=period_end)
    summary = compute_statement_summary(accounts, filtered)

    def section_rows(account_type):
        rows = []
        subtotal = 0.0
        for entry in summary["by_account"].values():
            if entry["account"]["account_type"] != account_type:
                continue
            rows.append([entry["account"]["account_code"], entry["account"]["name"], _fmt(entry["balance"])])
            subtotal += entry["balance"]
        return rows, subtotal

    rev_rows, rev_total = section_rows("revenue")
    exp_rows, exp_total = section_rows("expense")
    net_income = rev_total - exp_total

    rows = (
        [["", "[수익]", ""]] + rev_rows + [["", "매출총계", _fmt(rev_total)]]
        + [["", "[비용]", ""]] + exp_rows + [["", "비용총계", _fmt(exp_total)]]
        + [["", "당기순이익", _fmt(net_income)]]
    )

    title = f"손익계산서 ({period_start or '~'} ~ {period_end or '~'})"
    nodes = [
        title_node(title, y=720, font_size=16),
        {
            "type": "table",
            "x": MARGIN_PT, "y": 680,
            "col_widths": [50, 300, 118],
            "row_height": 16,
            "header": ["코드", "계정과목", "금액"],
            "rows": rows,
            "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
        },
    ]

    return {
        "summary": {"revenue_total": rev_total, "expense_total": exp_total, "net_income": net_income},
        "render_tree": {"pages": [new_page(nodes)]},
    }


def build_financial_statement_report(accounts: list[dict], journal_lines: list[dict], as_of_date, period_start, period_end) -> dict:
    """재무상태표 + 손익계산서를 하나의 다페이지 보고서로 결합."""
    bs = build_balance_sheet(accounts, journal_lines, as_of_date)
    is_ = build_income_statement(accounts, journal_lines, period_start, period_end)
    pages = bs["render_tree"]["pages"] + is_["render_tree"]["pages"]
    return {
        "summary": {**bs["summary"], **is_["summary"]},
        "render_tree": {"pages": pages},
    }
