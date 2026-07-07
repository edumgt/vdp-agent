# API 명세 (v2.0)

Base URL: `http://localhost:8081`

## 0) Health
### GET /health
`{"ok": true}`

---

## 1) 회사 / 계정과목
### POST /api/companies
```json
{ "name": "주식회사 조이아컴퍼니", "biz_reg_no": "123-45-67890", "fiscal_year_end_month": 12 }
```
→ `{ "company_id": "CORP-..." }`

### GET /api/companies
전체 목록.

### GET /api/companies/{company_id}
단건 조회.

### GET /api/accounts
전체 계정과목(chart of accounts) 조회.

---

## 2) 분개(Journal Entry)
### POST /api/journal-entries
```json
{
  "company_id": "CORP-0001",
  "entry_date": "2026-07-01",
  "description": "거래처 접대 - 한정식당",
  "lines": [
    { "account_code": "813", "debit": 60000, "credit": 0 },
    { "account_code": "102", "debit": 0, "credit": 60000 }
  ],
  "source_type": "manual"
}
```
- 차변/대변 합계가 일치하지 않으면 400.
- 라인이 2개인 단순분개는 등록 즉시 **계정과목 자동분류(classify_entry) job이 비동기로 enqueue**됩니다.

### GET /api/journal-entries?company_id=CORP-0001
### GET /api/journal-entries/{entry_id}
분개 + 라인 + 최신 ML 분류결과(`ml_classification`) 반환.

---

## 3) 증빙(Voucher) — OCR
### POST /api/vouchers (multipart/form-data)
필드: `company_id`, `voucher_type`(receipt|tax_invoice), `file`
→ `{ "voucher_id": "VCH-...", "status": "uploaded" }` — 업로드 즉시 `ocr_voucher` job enqueue.

### GET /api/vouchers?company_id=CORP-0001
### GET /api/vouchers/{voucher_id}
`ocr_raw_text`, `ocr_confidence`, `extracted_json`(사업자번호/금액/일자/거래처), `status` 포함.

---

## 4) ML 파이프라인
### POST /api/ml/classify-preview
```json
{ "description": "카카오T 택시 이용료" }
```
→ `{ "account_code": "822", "confidence": 0.13, "distribution": {...}, "model_version": "account-classifier-nb-v1" }`
(DB 기록 없이 즉시 추론)

### GET /api/ml/anomalies?company_id=CORP-0001&start=2026-01-01&end=2026-06-30
IsolationForest 기반 계정별 금액 이상치 목록(계산 시 `ml_anomalies`에 기록).

### GET /api/ml/forecast?company_id=CORP-0001&metric=revenue&periods_ahead=3
`metric`: `revenue` | `cash_flow`. Holt 지수평활(또는 데이터가 적으면 naive) 예측(계산 시 `ml_forecasts`에 기록).

---

## 5) 보고서(PDF)
### POST /api/reports/generate
```json
{
  "company_id": "CORP-0001",
  "report_type": "closing_report",
  "period_start": "2026-01-01",
  "period_end": "2026-06-30",
  "as_of_date": "2026-06-30",
  "beginning_wip": 0,
  "ending_wip": 0
}
```
`report_type`: `financial_statement` | `ledger` | `tax_summary` | `closing_report` | `company_dashboard`
→ `{ "report_id": "RPT-...", "status": "pending" }` (비동기 `generate_report` job)

### GET /api/reports/{report_id}
상태(`pending|running|done|failed`), `file_path`, `file_hash`, `source_snapshot` 등.

### GET /api/reports/{report_id}/pdf
완료된 PDF 다운로드(`status != done`이면 409).

### GET /api/companies/{company_id}/dashboard
PDF 없이 **즉시 계산**되는 웹 대시보드 JSON(재무요약/재무비율/수출비중/제조원가명세서/유형자산목록).
쿼리: `as_of_date`, `period_start`, `period_end` (선택, 기본값은 오늘/전체기간).

---

## 6) OpenDART 연동
### GET /api/dart/search?name=삼성전자
`DART_API_KEY` 있으면 실시간 조회, 없으면 fixture. → `{ "source": "live"|"fixture", "matches": [{corp_code, corp_name, stock_code, modify_date}] }`

### POST /api/dart/companies/{corp_code}/regenerate
```json
{ "company_id": "CORP-0001", "corp_name": "삼성전자", "bsns_year": "2023" }
```
→ `{ "report_id": "RPT-...", "status": "pending" }` — 비동기 `dart_regenerate` job.
완료 후 `GET /api/reports/{report_id}/pdf`로 다운로드(report_type=`dart_replica`).
