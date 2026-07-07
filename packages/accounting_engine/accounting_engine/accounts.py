"""계정과목(chart of accounts) 헬퍼."""

BS_TYPES = ("asset", "liability", "equity")
IS_TYPES = ("revenue", "expense")

TYPE_LABELS_KO = {
    "asset": "자산",
    "liability": "부채",
    "equity": "자본",
    "revenue": "수익",
    "expense": "비용",
}


def account_index(accounts: list[dict]) -> dict:
    """account_code -> account dict"""
    return {a["account_code"]: a for a in accounts}


def account_balance(account: dict, debit_sum: float, credit_sum: float) -> float:
    """계정의 정상잔액 방향으로 부호를 맞춘 잔액을 반환."""
    raw = debit_sum - credit_sum
    return raw if account["normal_balance"] == "debit" else -raw


def sum_lines_by_account(journal_lines: list[dict]) -> dict:
    """account_code -> {debit, credit} 합계"""
    totals: dict[str, dict] = {}
    for line in journal_lines:
        code = line["account_code"]
        bucket = totals.setdefault(code, {"debit": 0.0, "credit": 0.0})
        bucket["debit"] += float(line.get("debit") or 0)
        bucket["credit"] += float(line.get("credit") or 0)
    return totals
