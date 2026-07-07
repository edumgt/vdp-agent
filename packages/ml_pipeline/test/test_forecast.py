import pytest

from ml_pipeline.forecast import forecast_metric, monthly_series


def test_monthly_series_aggregates_by_year_month():
    lines = [
        {"entry_date": "2026-01-05", "debit": 100, "credit": 0},
        {"entry_date": "2026-01-20", "debit": 50, "credit": 0},
        {"entry_date": "2026-02-01", "debit": 0, "credit": 30},
    ]
    series = monthly_series(lines, lambda line: float(line["debit"]) - float(line["credit"]))
    assert series == [("2026-01", 150.0), ("2026-02", -30.0)]


def test_forecast_metric_naive_for_short_series():
    result = forecast_metric([100.0, 120.0], periods_ahead=2)
    assert result["model_version"] == "naive-last-value-v1"
    assert result["forecast"] == [120.0, 120.0]


def test_forecast_metric_holt_for_longer_series_with_trend():
    values = [100.0, 120.0, 140.0, 160.0, 180.0, 200.0]
    result = forecast_metric(values, periods_ahead=3)
    assert result["model_version"] == "holt-exponential-smoothing-v1"
    assert len(result["forecast"]) == 3
    # 상승 추세이므로 예측값도 마지막 실측치보다 커야 함
    assert result["forecast"][0] > values[-1]


def test_forecast_metric_requires_min_two_points():
    with pytest.raises(ValueError):
        forecast_metric([100.0], periods_ahead=1)
