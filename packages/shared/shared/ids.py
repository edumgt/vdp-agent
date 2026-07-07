import datetime
import os


def make_id(prefix: str) -> str:
    now = datetime.datetime.now()
    stamp = now.strftime("%Y%m%d")
    rand = os.urandom(3).hex()
    return f"{prefix}-{stamp}-{rand}".upper()
