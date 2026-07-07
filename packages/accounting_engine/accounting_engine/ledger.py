"""총계정원장(General Ledger) / 분개장(Journal Register) 렌더트리 빌더."""
from .accounts import account_index
from .page import MARGIN_PT, new_page, title_node

_ROWS_PER_PAGE = 26


def _fmt(n: float) -> str:
    return f"{n:,.0f}" if n else "-"


def build_general_ledger(accounts: list[dict], journal_lines: list[dict]) -> dict:
    """계정별로 페이지를 나누어 원장을 구성. 반환: {"pages": [...]}"""
    idx = account_index(accounts)
    by_account: dict[str, list] = {}
    for line in journal_lines:
        by_account.setdefault(line["account_code"], []).append(line)

    pages = []
    for code in sorted(by_account.keys()):
        account = idx.get(code, {"name": code, "normal_balance": "debit"})
        lines = sorted(by_account[code], key=lambda line: (line["entry_date"], line["entry_id"]))

        running = 0.0
        rows = []
        for line in lines:
            debit = float(line.get("debit") or 0)
            credit = float(line.get("credit") or 0)
            signed = (debit - credit) if account["normal_balance"] == "debit" else (credit - debit)
            running += signed
            rows.append([
                str(line["entry_date"]),
                line.get("description", ""),
                _fmt(debit),
                _fmt(credit),
                _fmt(running),
            ])

        nodes = [
            title_node(f"{code} {account.get('name', '')} — 총계정원장", y=720, font_size=16),
            {
                "type": "table",
                "x": MARGIN_PT, "y": 680,
                "col_widths": [70, 218, 60, 60, 60],
                "row_height": 18,
                "header": ["일자", "적요", "차변", "대변", "잔액"],
                "rows": rows,
                "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
            },
        ]
        pages.append(new_page(nodes))

    return {"pages": pages}


def build_journal_register(journal_lines: list[dict], accounts: list[dict]) -> dict:
    """전체 분개를 일자순으로 나열(분개장). 페이지당 _ROWS_PER_PAGE 행으로 페이지네이션."""
    idx = account_index(accounts)
    ordered = sorted(journal_lines, key=lambda line: (line["entry_date"], line["entry_id"]))

    rows = []
    for line in ordered:
        account = idx.get(line["account_code"], {"name": line["account_code"]})
        rows.append([
            str(line["entry_date"]),
            line.get("description", ""),
            f"{line['account_code']} {account.get('name', '')}",
            _fmt(float(line.get("debit") or 0)),
            _fmt(float(line.get("credit") or 0)),
        ])

    chunks = [rows[i:i + _ROWS_PER_PAGE] for i in range(0, len(rows), _ROWS_PER_PAGE)] or [[]]

    pages = []
    for i, chunk in enumerate(chunks):
        nodes = [
            title_node("분개장 (Journal Register)" + (f" — {i + 1}/{len(chunks)}" if len(chunks) > 1 else ""), y=720, font_size=16),
            {
                "type": "table",
                "x": MARGIN_PT, "y": 680,
                "col_widths": [70, 168, 130, 50, 50],
                "row_height": 18,
                "header": ["일자", "적요", "계정과목", "차변", "대변"],
                "rows": chunk,
                "style": {"font_key": "body", "font_size": 9, "header_font_size": 9},
            },
        ]
        pages.append(new_page(nodes))

    return {"pages": pages}
