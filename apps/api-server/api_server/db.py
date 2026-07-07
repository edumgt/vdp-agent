from accounting_data import get_conn, query as _query


def query(sql, params=None, fetch="all"):
    """단발성 쿼리 헬퍼(요청마다 connect/close). fetch='all'|'one'|None(쓰기 전용)."""
    conn = get_conn()
    try:
        result = _query(conn, sql, params, fetch)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
