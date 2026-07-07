import json
import os
from importlib import resources

from .fixture_provider import FixtureOcrProvider
from .provider import OcrProvider


def _load_default_fixtures() -> dict:
    with resources.files("ml_pipeline.data").joinpath("ocr_fixtures.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def get_provider(name: str | None = None, fixtures: dict | None = None) -> OcrProvider:
    """
    OCR_PROVIDER 환경변수(fixture|easyocr)에 따라 실제 구현체를 선택합니다.
    기본값은 fixture (오프라인/결정적) 이며, easyocr은 실제 사전학습 DL 모델을 로드합니다.
    """
    name = name or os.environ.get("OCR_PROVIDER", "fixture")
    if name == "easyocr":
        from .easyocr_provider import EasyOcrProvider
        return EasyOcrProvider()
    return FixtureOcrProvider(fixtures or _load_default_fixtures())
