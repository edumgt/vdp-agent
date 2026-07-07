from shared import make_id, env, now_iso


def test_make_id_prefix_and_format():
    mid = make_id("ORD")
    assert mid.startswith("ORD-")
    parts = mid.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 6  # 3 random bytes as hex


def test_env_fallback():
    assert env("__NOT_SET__", "default") == "default"


def test_now_iso_has_timezone():
    assert "+" in now_iso() or now_iso().endswith("Z")
