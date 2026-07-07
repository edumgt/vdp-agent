"""
이상거래(금액 이상치) 탐지.
- 알고리즘: scikit-learn IsolationForest (비지도 학습, 랜덤 파티셔닝 트리 앙상블)
- 선택 이유: 라벨(정상/이상) 데이터 없이도 동작하며, 정규분포를 가정하지 않아
  회계 거래처럼 왜곡된(skewed) 금액 분포에도 z-score보다 안정적입니다.
- 계정과목별로 별도 모델을 학습합니다(계정마다 정상 금액 스케일이 크게 다르기 때문).
- 프로덕션 고도화 경로: 금액 외에 요일/거래처/적요 임베딩 등 다변량 특징을 추가하고,
  Autoencoder 기반 재구성오차 이상탐지로 확장 가능합니다.
"""
import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_VERSION = "isolation-forest-v1"


def _line_amount(line: dict) -> float:
    return float(line.get("debit") or 0) + float(line.get("credit") or 0)


def detect_anomalies(journal_lines: list[dict], min_samples: int = 4, contamination: float = 0.15, random_state: int = 42) -> list[dict]:
    by_account: dict[str, list] = {}
    for line in journal_lines:
        by_account.setdefault(line["account_code"], []).append(line)

    results = []
    for account_code, lines in by_account.items():
        if len(lines) < min_samples:
            continue

        amounts = [_line_amount(line) for line in lines]
        X = np.array(amounts).reshape(-1, 1)

        model = IsolationForest(contamination=contamination, random_state=random_state, n_estimators=100)
        model.fit(X)
        predictions = model.predict(X)
        scores = model.decision_function(X)  # 높을수록 정상
        mean = float(np.mean(amounts)) if amounts else 0.0

        for line, pred, score, amount in zip(lines, predictions, scores, amounts):
            if pred != -1:
                continue
            ratio = (amount / mean) if mean else 0.0
            results.append({
                "entry_id": line["entry_id"],
                "account_code": account_code,
                "amount": amount,
                "score": float(-score),
                "is_anomaly": True,
                "reason": f"{account_code} 계정 평균({mean:,.0f}원) 대비 {ratio:.1f}배 금액",
                "model_version": MODEL_VERSION,
            })

    return results
