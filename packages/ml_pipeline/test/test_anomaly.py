from ml_pipeline.anomaly import detect_anomalies


def test_detect_anomalies_flags_large_outlier():
    lines = []
    for i in range(10):
        lines.append({"entry_id": f"E{i}", "account_code": "813", "debit": 50_000, "credit": 0, "entry_date": f"2026-01-{i+1:02d}"})
    # 명백한 이상치: 접대비가 평소의 40배
    lines.append({"entry_id": "E-OUT", "account_code": "813", "debit": 2_000_000, "credit": 0, "entry_date": "2026-01-20"})

    anomalies = detect_anomalies(lines, min_samples=4)
    flagged_ids = [a["entry_id"] for a in anomalies]
    assert "E-OUT" in flagged_ids
    entry = next(a for a in anomalies if a["entry_id"] == "E-OUT")
    assert entry["account_code"] == "813"
    assert entry["model_version"]


def test_detect_anomalies_skips_accounts_with_too_few_samples():
    lines = [
        {"entry_id": "E1", "account_code": "801", "debit": 1_000_000, "credit": 0, "entry_date": "2026-01-01"},
        {"entry_id": "E2", "account_code": "801", "debit": 50_000_000, "credit": 0, "entry_date": "2026-01-02"},
    ]
    anomalies = detect_anomalies(lines, min_samples=4)
    assert anomalies == []
