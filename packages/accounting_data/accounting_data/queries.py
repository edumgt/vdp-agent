"""
accounting_engine / ml_pipeline이 기대하는 입력 형태(list[dict])로 정규화된 Postgres 조회 헬퍼.
api-server(동기 대시보드 조회)와 worker(비동기 리포트 생성)가 동일 함수를 공유해
쿼리 로직이 두 곳에서 어긋나지 않도록 합니다.
"""
from .connection import query


def fetch_accounts(conn) -> list[dict]:
    return query(conn, "SELECT * FROM accounts ORDER BY account_code")


def fetch_journal_lines(conn, company_id: str, start=None, end=None) -> list[dict]:
    sql = """
        SELECT je.entry_id, je.entry_date, je.description, jl.account_code, jl.debit, jl.credit, jl.memo
        FROM journal_lines jl
        JOIN journal_entries je ON je.entry_id = jl.entry_id
        WHERE je.company_id = %s
    """
    params = [company_id]
    if start:
        sql += " AND je.entry_date >= %s"
        params.append(start)
    if end:
        sql += " AND je.entry_date <= %s"
        params.append(end)
    sql += " ORDER BY je.entry_date, je.entry_id"
    return query(conn, sql, params)


def fetch_tax_invoices(conn, company_id: str, start=None, end=None) -> list[dict]:
    sql = "SELECT * FROM tax_invoices WHERE company_id = %s"
    params = [company_id]
    if start:
        sql += " AND issue_date >= %s"
        params.append(start)
    if end:
        sql += " AND issue_date <= %s"
        params.append(end)
    sql += " ORDER BY issue_date"
    return query(conn, sql, params)


def fetch_fixed_assets(conn, company_id: str) -> list[dict]:
    return query(conn, "SELECT * FROM fixed_assets WHERE company_id = %s ORDER BY acquisition_date", [company_id])


def fetch_company(conn, company_id: str) -> dict | None:
    return query(conn, "SELECT * FROM companies WHERE company_id = %s", [company_id], fetch="one")
