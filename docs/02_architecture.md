# 시스템 아키텍처/워크플로우 (v2.0)

## 1) 구성
- Web Admin / Web Client: Vanilla JS 정적 페이지 (fetch 기반 REST 호출)
- API Server: Flask REST API (인증 없음, MVP) — 회사/분개/증빙/보고서/ML/DART 엔드포인트
- Worker: RQ(Redis Queue) 비동기 작업자 — OCR, 계정분류, PDF 생성, DART 재현
- DB(Postgres), Queue(Redis), Storage(Local/MinIO)
- 외부 연동: OpenDART Open API

---

## 2) 전체 구성도

```mermaid
flowchart LR
  WA[Web Admin] --> API[Flask API Server]
  WC[Web Client] --> API
  API -->|CRUD| DB[(Postgres)]
  API -->|enqueue job| Q[(Redis / RQ)]
  W[RQ Worker] -->|pickup job| Q
  W -->|read/write| DB
  W --> AE[accounting_engine]
  W --> ML[ml_pipeline]
  W --> DI[dart_integration]
  AE --> PE[pdf_engine]
  ML --> PE
  DI --> PE
  PE -->|save PDF| S[(Storage: Local/MinIO)]
  DI -->|live or fixture| DART[(OpenDART Open API)]
  API -->|download| S
```

---

## 3) 기장 보고서 생성 플로우

```mermaid
sequenceDiagram
  autonumber
  participant U as Admin/Client
  participant A as API Server
  participant DB as Postgres
  participant Q as Redis/RQ
  participant W as Worker
  participant AE as accounting_engine
  participant ML as ml_pipeline
  participant PE as pdf_engine
  participant S as Storage

  U->>A: POST /api/reports/generate (report_type, period)
  A->>DB: pdf_reports insert (pending)
  A->>Q: enqueue generate_report
  W->>Q: pickup
  W->>DB: accounts/journal_lines/tax_invoices/fixed_assets 조회
  W->>AE: 재무제표/원장/세금정리표/제조원가/유형자산/대시보드 빌드
  alt closing_report
    W->>ML: 이상탐지 + 분류신뢰도 + 예측
    ML-->>W: 결과
  end
  W->>PE: render_pdf(render_tree, font_map)
  PE-->>W: PDF 파일 + hash
  W->>DB: pdf_reports 상태=done, file_path/hash 저장
  U->>A: GET /api/reports/{id}/pdf
  A->>S: 파일 read/stream
  A-->>U: PDF 응답
```

---

## 4) 증빙 OCR → 분개 보조 플로우

```mermaid
flowchart TB
  UP[증빙 업로드: 영수증/세금계산서] --> V[vouchers insert status=uploaded]
  V --> J1[enqueue ocr_voucher]
  J1 --> OCR{OCR Provider}
  OCR -->|fixture 기본값| TXT[결정적 텍스트]
  OCR -->|OCR_PROVIDER=easyocr| DL[EasyOCR CRNN DL 모델]
  TXT --> EXT[정규식 기반 필드추출]
  DL --> EXT
  EXT --> V2[vouchers.extracted_json 저장, status=ocr_done]

  JE[분개 등록: 2줄 단순분개] --> J2[enqueue classify_entry]
  J2 --> CLS[Naive Bayes 계정분류기]
  CLS --> MC[ml_classifications 저장: 예측계정/신뢰도/오버라이드여부]
```

---

## 5) OpenDART 재현 플로우

```mermaid
sequenceDiagram
  participant U as Admin
  participant A as API Server
  participant W as Worker
  participant DI as dart_integration
  participant DART as OpenDART
  participant PE as pdf_engine

  U->>A: GET /api/dart/search?name=삼성전자
  A->>DI: search_corp_code
  DI->>DART: corpCode.xml (키 있으면 실호출, 없으면 fixture)
  DART-->>DI: corp_code 목록
  DI-->>A: 검색 결과
  U->>A: POST /api/dart/companies/{corp_code}/regenerate
  A->>W: enqueue dart_regenerate
  W->>DI: fetch_financial_statements
  DI->>DART: fnlttSinglAcntAll.json
  DART-->>DI: 재무제표 원본
  W->>DI: build_dart_replica_render_tree (표준계정명 매핑 + 재무비율)
  W->>PE: render_pdf
  PE-->>W: PDF 저장
```

---

## 6) 핵심 설계 포인트
- **웹/워커 분리**: 동기 API 요청과 무거운 PDF/OCR/외부API 작업을 비동기로 분리.
- **패키지 분리**: accounting_engine(회계 로직) / ml_pipeline(ML/DL) / pdf_engine(렌더링) / dart_integration(외부연동)을 독립 모듈화해 단위테스트 용이.
- **렌더트리 공통 포맷**: 모든 보고서 빌더가 `{"pages":[{"page":..,"nodes":[text|table|bar_chart]}]}` 동일 포맷을 반환 → pdf_engine 하나로 전 문서 렌더링.
- **ML 결과 추적성**: 모든 분류/이상탐지/예측 결과에 `model_version`을 기록해 회귀 비교/감사 가능.
- **오프라인 대체 경로**: EasyOCR/OpenDART 모두 "실제 연동"과 "fixture 대체"를 동일 인터페이스로 제공해 네트워크/키 없이도 개발·테스트 가능.
