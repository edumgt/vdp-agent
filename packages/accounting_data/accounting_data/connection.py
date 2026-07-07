import os

import psycopg2
import psycopg2.extras

# NUMERIC(...) 컬럼을 Decimal 대신 float으로 반환(JSON 직렬화/ML 파이프라인 입력 편의)
_FLOAT_NUMERIC = psycopg2.extensions.new_type((1700,), "NUMERIC_FLOAT", lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(_FLOAT_NUMERIC)


def _env(name, fallback=None):
    return os.environ.get(name, fallback)


def get_conn():
    conn = psycopg2.connect(
        host=_env("POSTGRES_HOST", "localhost"),
        port=int(_env("POSTGRES_PORT", "5432")),
        dbname=_env("POSTGRES_DB", "joya"),
        user=_env("POSTGRES_USER", "joya"),
        password=_env("POSTGRES_PASSWORD", "joya1234"),
    )
    return conn


def query(conn, sql, params=None, fetch="all"):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params or [])
        if fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        return None
