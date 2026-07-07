"""
EasyOCR(PyTorch 기반 CRNN: CNN 특징추출 + LSTM 시퀀스 인식 + CTC 디코딩) 실제 사전학습 DL 모델 연동.
- 무거운 의존성(torch, torchvision)이 필요해 requirements-ocr.txt로 분리되어 있습니다.
- 최초 실행 시 한국어/영어 인식 가중치(수십~백여 MB)를 다운로드/캐시합니다(네트워크 필요).
"""
from .provider import OcrProvider

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
        except ImportError as e:
            raise ImportError(
                "easyocr가 설치되어 있지 않습니다. `pip install -r requirements-ocr.txt` 후 다시 시도하세요."
            ) from e
        _reader = easyocr.Reader(["ko", "en"], gpu=False)
    return _reader


class EasyOcrProvider(OcrProvider):
    def extract_text(self, image_path: str) -> dict:
        reader = _get_reader()
        results = reader.readtext(image_path, detail=1)
        if not results:
            return {"text": "", "confidence": 0.0, "engine": "easyocr"}
        lines = [r[1] for r in results]
        confidences = [float(r[2]) for r in results]
        return {
            "text": "\n".join(lines),
            "confidence": sum(confidences) / len(confidences),
            "engine": "easyocr",
        }
