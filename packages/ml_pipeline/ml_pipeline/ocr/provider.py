from abc import ABC, abstractmethod


class OcrProvider(ABC):
    """OCR 엔진 추상화. 실제 엔진(EasyOCR)과 오프라인 fixture 엔진을 동일 인터페이스로 다룹니다."""

    @abstractmethod
    def extract_text(self, image_path: str) -> dict:
        """반환: {"text": str, "confidence": float(0~1), "engine": str}"""
        raise NotImplementedError
