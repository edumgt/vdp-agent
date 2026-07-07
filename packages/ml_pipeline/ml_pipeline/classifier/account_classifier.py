"""
계정과목 자동분류기.
- 알고리즘: TF-IDF(문자 2~3-gram) + Multinomial Naive Bayes
- 선택 이유: 한국어는 형태소 분석기 없이 공백 기준 토큰화가 부정확하므로,
  문자 n-gram 기반 벡터화가 별도 형태소 분석기 없이도 안정적으로 동작합니다.
  Naive Bayes는 적은 라벨 데이터(수십~수백 건)에서도 과적합 없이 합리적인 baseline을 제공합니다.
- 프로덕션 고도화 경로: 라벨 데이터가 수만 건 이상 축적되면 KoBERT/RoBERTa 파인튜닝 또는
  임베딩 기반 분류(문장 임베딩 + 분류기 헤드)로 전환해 정확도를 높일 수 있습니다.
"""
import json
from importlib import resources
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_VERSION = "account-classifier-nb-v1"


def load_labeled_data() -> list[dict]:
    with resources.files("ml_pipeline.data").joinpath("labeled_transactions.json").open("r", encoding="utf-8") as f:
        return json.load(f)


class AccountClassifier:
    def __init__(self, pipeline: Pipeline):
        self._pipeline = pipeline

    @classmethod
    def train(cls, examples: list[dict]) -> "AccountClassifier":
        texts = [e["text"] for e in examples]
        labels = [e["account_code"] for e in examples]
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3), min_df=1)),
            ("nb", MultinomialNB()),
        ])
        pipeline.fit(texts, labels)
        return cls(pipeline)

    @classmethod
    def load_default(cls) -> "AccountClassifier":
        """models/account_classifier.joblib가 있으면 로드하고, 없으면 라벨 데이터로 즉시 학습(개발 편의)."""
        model_path = resources.files("ml_pipeline.models").joinpath("account_classifier.joblib")
        if Path(str(model_path)).exists():
            return cls(joblib.load(str(model_path)))
        return cls.train(load_labeled_data())

    def save(self, path: str) -> None:
        joblib.dump(self._pipeline, path)

    def predict(self, text: str) -> dict:
        proba = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_
        distribution = dict(sorted(zip(classes, proba), key=lambda kv: -kv[1]))
        best_code = max(distribution, key=distribution.get)
        return {
            "account_code": best_code,
            "confidence": float(distribution[best_code]),
            "distribution": {k: float(v) for k, v in distribution.items()},
            "model_version": MODEL_VERSION,
        }
