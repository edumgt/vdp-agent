"""scripts/*.py 공용 헬퍼: .env 로드 + accounting_data.get_conn 재노출."""
import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

from accounting_data import get_conn  # noqa: E402

__all__ = ["get_conn"]
