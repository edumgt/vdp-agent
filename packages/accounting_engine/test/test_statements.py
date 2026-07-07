from accounting_engine.statements import build_balance_sheet, build_income_statement, build_financial_statement_report


def test_balance_sheet_totals(accounts, journal_lines):
    result = build_balance_sheet(accounts, journal_lines)
    summary = result["summary"]
    assert summary["asset_total"] == 11_500_000  # 102 보통예금 잔액
    assert summary["liability_total"] == 200_000
    assert summary["equity_total"] == 10_000_000
    assert result["render_tree"]["pages"][0]["nodes"][1]["type"] == "table"


def test_income_statement_totals(accounts, journal_lines):
    result = build_income_statement(accounts, journal_lines, "2026-01-01", "2026-02-28")
    summary = result["summary"]
    assert summary["revenue_total"] == 3_000_000
    assert summary["expense_total"] == 1_700_000
    assert summary["net_income"] == 1_300_000


def test_income_statement_period_filter_excludes_out_of_range(accounts, journal_lines):
    # 1월만 필터링하면 2월에 발생한 급여(사무용품 외상매입 200,000)는 제외되어야 함
    result = build_income_statement(accounts, journal_lines, "2026-01-01", "2026-01-31")
    assert result["summary"]["expense_total"] == 1_500_000


def test_financial_statement_report_combines_pages(accounts, journal_lines):
    result = build_financial_statement_report(accounts, journal_lines, "2026-02-28", "2026-01-01", "2026-02-28")
    assert len(result["render_tree"]["pages"]) == 2
    assert "asset_total" in result["summary"]
    assert "net_income" in result["summary"]
