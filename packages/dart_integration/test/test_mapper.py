from dart_integration.client import fetch_financial_statements
from dart_integration.mapper import build_dart_replica_render_tree, map_to_summary


def test_map_to_summary_extracts_key_figures():
    items = fetch_financial_statements("00126380", "2023")["items"]
    summary = map_to_summary(items)
    assert summary["asset_total"] == 455905980000000.0
    assert summary["liability_total"] == 92228115000000.0
    assert summary["equity_total"] == 363677865000000.0
    assert summary["net_income"] == 15487100000000.0


def test_build_dart_replica_render_tree_structure():
    items = fetch_financial_statements("00126380", "2023")["items"]
    result = build_dart_replica_render_tree("삼성전자", "2023", items, source="fixture")
    pages = result["render_tree"]["pages"]
    assert len(pages) == 2
    assert pages[0]["nodes"][2]["type"] == "table"
    assert result["ratios"]["equity_ratio_pct"] is not None
