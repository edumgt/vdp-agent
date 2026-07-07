
from ml_pipeline.ocr import FixtureOcrProvider, extract_fields, get_provider


def test_fixture_provider_returns_matching_text():
    provider = FixtureOcrProvider({"a.png": {"text": "hello", "confidence": 0.9}})
    result = provider.extract_text("/tmp/whatever/a.png")
    assert result["text"] == "hello"
    assert result["engine"] == "fixture"


def test_fixture_provider_falls_back_to_default():
    provider = FixtureOcrProvider({"default": {"text": "fallback"}})
    result = provider.extract_text("/tmp/unknown.png")
    assert result["text"] == "fallback"


def test_get_provider_defaults_to_fixture(monkeypatch):
    monkeypatch.delenv("OCR_PROVIDER", raising=False)
    provider = get_provider()
    assert isinstance(provider, FixtureOcrProvider)
    result = provider.extract_text("receipt_001.png")
    assert "스타벅스" in result["text"]


def test_extract_fields_from_tax_invoice_text():
    text = (
        "전자세금계산서\n"
        "공급자 사업자등록번호 214-81-11112\n"
        "작성일자 2026-02-10\n"
        "공급가액 3,000,000원\n"
        "세액 300,000원\n"
        "합계금액 3,300,000원\n"
    )
    fields = extract_fields(text)
    assert fields["biz_reg_no"] == "214-81-11112"
    assert fields["issue_date"] == "2026-02-10"
    assert fields["supply_amount"] == 3_000_000
    assert fields["tax_amount"] == 300_000
    assert fields["total_amount"] == 3_300_000


def test_extract_fields_handles_missing_values_gracefully():
    fields = extract_fields("알 수 없는 텍스트")
    assert fields["biz_reg_no"] is None
    assert fields["issue_date"] is None
    assert fields["supply_amount"] is None
