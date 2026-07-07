from unittest.mock import MagicMock

from accounting_data.queries import fetch_journal_lines, fetch_tax_invoices


def _mock_conn(rows):
    cur = MagicMock()
    cur.fetchall.return_value = rows
    cur.__enter__.return_value = cur
    cur.__exit__.return_value = False
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


def test_fetch_journal_lines_applies_date_filters():
    conn, cur = _mock_conn([])
    fetch_journal_lines(conn, "CORP-0001", start="2026-01-01", end="2026-01-31")
    sql, params = cur.execute.call_args[0]
    assert "entry_date >= %s" in sql
    assert "entry_date <= %s" in sql
    assert params == ["CORP-0001", "2026-01-01", "2026-01-31"]


def test_fetch_journal_lines_without_date_filters():
    conn, cur = _mock_conn([])
    fetch_journal_lines(conn, "CORP-0001")
    sql, params = cur.execute.call_args[0]
    assert "entry_date >=" not in sql
    assert params == ["CORP-0001"]


def test_fetch_tax_invoices_filters_by_company():
    conn, cur = _mock_conn([])
    fetch_tax_invoices(conn, "CORP-0001", start="2026-01-01")
    sql, params = cur.execute.call_args[0]
    assert "company_id = %s" in sql
    assert params == ["CORP-0001", "2026-01-01"]
