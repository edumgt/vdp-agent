from accounting_engine.ledger import build_general_ledger, build_journal_register


def test_general_ledger_running_balance_per_account(accounts, journal_lines):
    result = build_general_ledger(accounts, journal_lines)
    # 계정코드 오름차순: 102, 201, 331, 401, 801 (101은 거래 없음 -> 페이지 없음)
    page_codes = [p["nodes"][0]["text"].split(" ")[0] for p in result["pages"]]
    assert page_codes == ["102", "201", "331", "401", "801"]

    page_102 = result["pages"][0]
    rows = page_102["nodes"][1]["rows"]
    # 10,000,000 입금 -> 13,000,000(매출 입금 후) -> 11,500,000(급여 지급 후)
    assert rows[-1][-1] == "11,500,000"


def test_journal_register_row_count_and_order(accounts, journal_lines):
    result = build_journal_register(journal_lines, accounts)
    rows = result["pages"][0]["nodes"][1]["rows"]
    assert len(rows) == len(journal_lines)
    dates = [r[0] for r in rows]
    assert dates == sorted(dates)


def test_journal_register_paginates_long_lists(accounts):
    many_lines = []
    for i in range(60):
        many_lines.append({
            "entry_id": f"E{i}", "entry_date": f"2026-01-{(i % 28) + 1:02d}",
            "description": "테스트 거래", "account_code": "801", "debit": 1000, "credit": 0,
        })
    result = build_journal_register(many_lines, accounts)
    assert len(result["pages"]) == 3  # 60 rows / 26 per page -> 3 pages
