from accounting_engine.closing_report import build_closing_report


def test_closing_report_structure():
    result = build_closing_report(
        company_name="주식회사 조이아컴퍼니",
        period_label="2026-01 ~ 2026-06",
        bs_summary={"asset_total": 11_500_000, "liability_total": 200_000, "equity_total": 10_000_000},
        is_summary={"revenue_total": 3_000_000, "expense_total": 1_700_000, "net_income": 1_300_000},
        ratios={"debt_ratio_pct": 2.0, "equity_ratio_pct": 86.96, "current_ratio_pct": None, "net_margin_pct": 43.33},
        ml_summary={
            "anomaly_count": 2,
            "avg_classification_confidence": 0.87,
            "forecast_metric_label": "다음달 현금흐름 예측",
            "forecast_value": 4_200_000,
        },
        monthly_trend={"categories": ["1월", "2월", "3월"], "values": [1_000_000, 1_500_000, 900_000], "title": "월별 매출"},
    )
    pages = result["render_tree"]["pages"]
    assert len(pages) == 2
    assert pages[1]["nodes"][1]["type"] == "bar_chart"
    kpi_table = pages[0]["nodes"][3]
    assert ["자산총계", "11,500,000"] in kpi_table["rows"]
    ml_table = pages[0]["nodes"][5]
    assert ["이상거래 탐지 건수", "2"] in ml_table["rows"]
