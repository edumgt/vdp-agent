#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db_util import get_conn  # noqa: E402

SQL_PATH = Path(__file__).resolve().parent.parent / "infra" / "db" / "migrations" / "001_init.sql"


def main():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_PATH.read_text(encoding="utf-8"))
        conn.commit()
        print("[db_migrate] OK")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
