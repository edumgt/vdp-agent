from accounting_engine.ratios import compute_export_ratio, compute_ratios


def test_compute_ratios_basic():
    bs = {"asset_total": 10_000_000, "liability_total": 2_000_000, "equity_total": 8_000_000}
    is_ = {"revenue_total": 5_000_000, "net_income": 1_000_000}
    ratios = compute_ratios(bs, is_)
    assert ratios["debt_ratio_pct"] == 25.0
    assert ratios["equity_ratio_pct"] == 80.0
    assert ratios["net_margin_pct"] == 20.0


def test_compute_ratios_handles_zero_denominators():
    ratios = compute_ratios({"asset_total": 0, "liability_total": 0, "equity_total": 0}, {"revenue_total": 0, "net_income": 0})
    assert ratios["debt_ratio_pct"] is None
    assert ratios["net_margin_pct"] is None


def test_compute_export_ratio():
    invoices = [
        {"direction": "sales", "market": "domestic", "supply_amount": 700_000},
        {"direction": "sales", "market": "export", "supply_amount": 300_000},
        {"direction": "purchase", "market": "domestic", "supply_amount": 999_999},  # 매입은 제외
    ]
    assert compute_export_ratio(invoices) == 30.0


def test_compute_export_ratio_none_when_no_sales():
    assert compute_export_ratio([{"direction": "purchase", "market": "domestic", "supply_amount": 100}]) is None
