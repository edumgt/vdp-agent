"""
OCR 텍스트에서 정형 필드를 뽑아내는 정규식 기반 추출기.
- OCR(EasyOCR/DL 모델)은 "이미지 -> 텍스트" 변환만 담당하고, 텍스트 -> 구조화 데이터는
  본 모듈이 규칙 기반으로 처리합니다.
- 프로덕션 고도화 경로: 라벨링된 영수증/세금계산서 이미지가 축적되면 LayoutLM/Donut 같은
  레이아웃 인지 문서이해(Document AI) 모델로 교체해 표 형태 문서에서도 정확도를 높일 수 있습니다.
"""
import re

_BIZ_REG_NO = re.compile(r"\d{3}-\d{2}-\d{5}")
_DATE = re.compile(r"(\d{4})[.\-년]\s?(\d{1,2})[.\-월]\s?(\d{1,2})일?")
_SUPPLY = re.compile(r"공급가액\s*([0-9,]+)\s*원?")
_TAX = re.compile(r"세액\s*([0-9,]+)\s*원?")
_TOTAL = re.compile(r"(?:합계금액|합계)\s*([0-9,]+)\s*원?")


def _to_number(s: str | None):
    if not s:
        return None
    return int(s.replace(",", ""))


def extract_fields(text: str) -> dict:
    biz_reg_match = _BIZ_REG_NO.search(text)
    date_match = _DATE.search(text)
    supply_match = _SUPPLY.search(text)
    tax_match = _TAX.search(text)
    total_match = _TOTAL.search(text)

    issue_date = None
    if date_match:
        y, m, d = date_match.groups()
        issue_date = f"{y}-{int(m):02d}-{int(d):02d}"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    counterparty_name = lines[0] if lines else None

    return {
        "biz_reg_no": biz_reg_match.group(0) if biz_reg_match else None,
        "issue_date": issue_date,
        "supply_amount": _to_number(supply_match.group(1) if supply_match else None),
        "tax_amount": _to_number(tax_match.group(1) if tax_match else None),
        "total_amount": _to_number(total_match.group(1) if total_match else None),
        "counterparty_name": counterparty_name,
    }
