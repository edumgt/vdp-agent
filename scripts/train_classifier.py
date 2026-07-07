#!/usr/bin/env python3
"""
계정과목 자동분류기 재학습.
packages/ml_pipeline/ml_pipeline/data/labeled_transactions.json 라벨 데이터를 기반으로
TF-IDF(char n-gram) + Multinomial Naive Bayes를 학습해 모델 아티팩트를 저장합니다.
"""
from pathlib import Path

from ml_pipeline.classifier import AccountClassifier, load_labeled_data

MODEL_PATH = Path(__file__).resolve().parent.parent / "packages" / "ml_pipeline" / "ml_pipeline" / "models" / "account_classifier.joblib"

if __name__ == "__main__":
    examples = load_labeled_data()
    print(f"[train_classifier] 라벨 데이터 {len(examples)}건으로 학습 시작")
    clf = AccountClassifier.train(examples)
    clf.save(str(MODEL_PATH))
    print(f"[train_classifier] 저장 완료: {MODEL_PATH}")
