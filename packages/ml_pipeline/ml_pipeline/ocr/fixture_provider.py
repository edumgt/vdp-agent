import os

from .provider import OcrProvider


class FixtureOcrProvider(OcrProvider):
    """
    네트워크/GPU 없이 결정적으로 동작하는 오프라인 OCR 대역.
    파일명(basename) 기준으로 고정 텍스트를 반환하며, 매칭되는 fixture가 없으면 "default" 키를 사용합니다.
    자동화 테스트/기본 실행 경로에서 사용하고, 실제 운영에서는 EasyOcrProvider로 교체합니다.
    """

    def __init__(self, fixtures: dict):
        self._fixtures = fixtures

    def extract_text(self, image_path: str) -> dict:
        key = os.path.basename(image_path)
        fixture = self._fixtures.get(key) or self._fixtures.get("default")
        if fixture is None:
            raise KeyError(f"fixture OCR 텍스트를 찾을 수 없습니다: {key}")
        return {"text": fixture["text"], "confidence": fixture.get("confidence", 0.95), "engine": "fixture"}
