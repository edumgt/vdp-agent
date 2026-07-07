"""
현금흐름/매출 예측.
- 알고리즘: statsmodels ExponentialSmoothing (Holt 선형 지수평활, trend='add')
- 선택 이유: 월 단위 회계 데이터는 보통 수개월~수년 규모라 LSTM/Prophet 같은
  대용량 시계열 모델을 학습하기엔 데이터가 부족한 경우가 많습니다. Holt 지수평활은
  적은 데이터로도 추세(trend)를 반영한 baseline 예측을 안정적으로 제공합니다.
- 프로덕션 고도화 경로: 24개월 이상의 데이터가 누적되면 Prophet(계절성 반영) 또는
  LSTM/Temporal Fusion Transformer 기반 다변량 예측으로 전환할 수 있습니다.
"""
from collections import defaultdict

HOLT_MODEL_VERSION = "holt-exponential-smoothing-v1"
NAIVE_MODEL_VERSION = "naive-last-value-v1"


def monthly_series(journal_lines: list[dict], value_fn) -> list[tuple[str, float]]:
    """journal_lines를 YYYY-MM 단위로 집계. value_fn(line) -> 부호 있는 금액."""
    totals: dict[str, float] = defaultdict(float)
    for line in journal_lines:
        period = str(line["entry_date"])[:7]
        totals[period] += value_fn(line)
    return sorted(totals.items())


def forecast_metric(values: list[float], periods_ahead: int = 3) -> dict:
    n = len(values)
    if n < 2:
        raise ValueError("예측에는 최소 2개월치 데이터가 필요합니다.")

    if n < 4:
        # 데이터가 적을 때는 Holt 과적합 위험이 있어 단순 최근값 반복(naive)으로 대체
        last = values[-1]
        forecast = [last] * periods_ahead
        return {"forecast": forecast, "model_version": NAIVE_MODEL_VERSION}

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(values, trend="add", seasonal=None, initialization_method="estimated")
    fit = model.fit()
    forecast = fit.forecast(periods_ahead).tolist()
    return {"forecast": forecast, "model_version": HOLT_MODEL_VERSION}
