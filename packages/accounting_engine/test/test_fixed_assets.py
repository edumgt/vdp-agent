from accounting_engine.fixed_assets import build_fixed_asset_list, compute_depreciation


def test_compute_depreciation_straight_line_at_midlife():
    asset = {
        "acquisition_date": "2024-01-01",
        "acquisition_cost": 10_000_000,
        "useful_life_years": 5,
        "salvage_value": 0,
    }
    # 2026-01-01 -> 정확히 2년 경과, 내용연수 5년 -> 40% 상각
    result = compute_depreciation(asset, "2026-01-01")
    assert abs(result["accumulated_depreciation"] - 4_000_000) < 20_000
    assert abs(result["book_value"] - 6_000_000) < 20_000


def test_compute_depreciation_caps_at_useful_life():
    asset = {
        "acquisition_date": "2010-01-01",
        "acquisition_cost": 1_000_000,
        "useful_life_years": 3,
        "salvage_value": 100_000,
    }
    result = compute_depreciation(asset, "2026-01-01")  # 내용연수를 훨씬 초과
    assert result["accumulated_depreciation"] == 900_000
    assert result["book_value"] == 100_000


def test_build_fixed_asset_list_totals():
    assets = [
        {"asset_id": "FA1", "name": "노트북", "account_code": "172", "acquisition_date": "2024-01-01", "acquisition_cost": 2_000_000, "useful_life_years": 4, "salvage_value": 0},
        {"asset_id": "FA2", "name": "차량", "account_code": "208", "acquisition_date": "2023-01-01", "acquisition_cost": 20_000_000, "useful_life_years": 5, "salvage_value": 2_000_000},
    ]
    result = build_fixed_asset_list(assets, "2026-01-01")
    assert result["summary"]["total_cost"] == 22_000_000
    last_row = result["render_tree"]["pages"][0]["nodes"][1]["rows"][-1]
    assert last_row[0] == "합계"
