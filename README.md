# 법인 기장(회계) PDF 생성 모듈 — AI/ML 기반 회계 자동화 플랫폼

본 레포는 법인의 회계 데이터를 기반으로 **재무제표/총계정원장·분개장/세금계산서 정리표/결산보고서/기업 대시보드** PDF를 생성하고,
증빙 OCR·계정과목 자동분류·이상거래 탐지·현금흐름 예측 등 **ML/DL 파이프라인**을 결합한 회계 자동화 모듈입니다.
추가로 **OpenDART(전자공시시스템)** 연동을 통해 외부 공시 기업을 검색하고, 해당 재무제표를 본 모듈의 PDF 템플릿으로 재현할 수 있습니다.

- 백엔드/ML/PDF 엔진: **Python** (Flask + RQ + scikit-learn + statsmodels + ReportLab)
- 프론트엔드: **Vanilla JS**(프레임워크/번들러 없음)
- 인프라: Postgres / Redis / (옵션)MinIO / Docker Compose

> ⚠️ 도입한 ML/DL 알고리즘의 문제정의·선택이유·한계·프로덕션 고도화 경로는 `docs/08_techstack_workflow.md`에 상세히 기술되어 있습니다.

---

## 빠른 시작(로컬)

### 1) 요구사항
- Python 3.10+
- Docker / Docker Compose (Postgres/Redis 로컬 기동용)

### 2) 실행
```bash
# 1) 환경변수 준비
cp .env.example .env

# 2) 인프라(Postgres/Redis/MinIO) 기동
python scripts/dev_up.py            # 또는: docker compose -f infra/docker/docker-compose.yml up -d

# 3) 파이썬 가상환경 + 의존성 설치
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 테스트/린트용(선택)

# 4) DB 마이그레이션/시드
python scripts/db_migrate.py
python scripts/db_seed.py

# 5) 폰트 배치 (라이선스 확인된 TTF/OTF를 assets/fonts에 배치, 레포에는 미포함)
#    docs/04_font_policy.md 참고

# 6) API 서버 / 워커 실행
python apps/api-server/wsgi.py            # http://localhost:8081
python apps/worker/run_worker.py           # 별도 터미널

# 7) 프론트엔드(정적 서빙, 번들러 불필요)
python -m http.server 3002 --directory apps/web-admin   # 관리자 콘솔
python -m http.server 3001 --directory apps/web-client  # 법인 담당자 포털
```

### 3) 샘플 보고서 생성 (API 없이 바로 확인)
```bash
python scripts/demo_generate_reports.py
# storage/pdfs/demo_*.pdf 5종 생성 확인
```

### 4) API로 전체 플로우 확인
```bash
curl -X POST http://localhost:8081/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"company_id":"CORP-0001","report_type":"closing_report","period_start":"2026-01-01","period_end":"2026-06-30","as_of_date":"2026-06-30"}'
# -> {"report_id": "RPT-...", "status": "pending"}

curl http://localhost:8081/api/reports/<REPORT_ID>
curl -L http://localhost:8081/api/reports/<REPORT_ID>/pdf -o report.pdf
```

---

## 문서
- 개요: `docs/00_overview.md`
- 요구사항/범위: `docs/01_requirements.md`
- 아키텍처/워크플로우(mermaid): `docs/02_architecture.md`
- 렌더트리/문서 템플릿 규격: `docs/03_template_spec.md`
- 폰트 정책(임베딩/라이선스): `docs/04_font_policy.md`
- API 명세: `docs/05_api_spec.md`
- 산출물 검증 체크리스트: `docs/06_preflight_checklist.md`
- 배포 가이드(Docker): `docs/07_deploy_guide.md`
- **기술스택 & ML/DL 알고리즘 상세**: `docs/08_techstack_workflow.md`

---

## 레포 구조
```
apps/
  api-server/   Flask REST API
  worker/       RQ 워커(OCR/분류/PDF생성/DART재현 비동기 작업)
  web-admin/    관리자 콘솔 (Vanilla JS)
  web-client/   법인 담당자 포털 (Vanilla JS)
packages/
  shared/             공통 유틸
  pdf_engine/         ReportLab 렌더러(text/table/bar_chart, 폰트 임베딩, bleed)
  accounting_engine/  원장/재무제표/세금계산서정리표/결산보고서/제조원가명세서/유형자산/기업대시보드 빌더
  accounting_data/    api-server/worker 공용 Postgres 조회 헬퍼
  ml_pipeline/        OCR+정보추출 / 계정과목분류 / 이상거래탐지 / 현금흐름·매출예측
  dart_integration/   OpenDART 연동(회사검색/재무제표 수집) + 내부 템플릿 재현
infra/
  db/       마이그레이션/시드 SQL
  docker/   Dockerfile들 + docker-compose.yml
scripts/    dev_up/down, db_migrate/seed, lint, test, train_classifier, demo_generate_reports
```

---

## 라이선스/폰트
본 레포는 **폰트 바이너리(.ttf/.otf)를 포함하지 않습니다.**
- 임베딩 허용 폰트를 `assets/fonts`에 배치하고 `.env`의 `FONTS_DIR`을 확인하세요.
- 자세한 정책은 `docs/04_font_policy.md` 참고.
