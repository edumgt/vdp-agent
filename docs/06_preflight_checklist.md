# 산출물(재무 PDF) 검증 체크리스트 (v2.0)

> 목표: 잘못된 재무 수치·분개 불일치·폰트 치환으로 인한 문서 사고 방지

## 1) 회계 정합성 검사
- [ ] 모든 분개의 차변 합계 == 대변 합계인가? (`POST /api/journal-entries`에서 강제 검증)
- [ ] 재무상태표의 자산총계/부채총계/자본총계가 `accounting_engine.compute_statement_summary` 집계와 일치하는가?
- [ ] 결산 전(수익/비용 미마감) 상태에서는 `자산총계 ≠ 부채+자본총계`가 정상(당기순이익 차이)임을 인지하고 있는가?

## 2) PDF 산출물 검사
- [ ] PDF 내 폰트가 지정 폰트만 사용되었는가? (`pdf_engine.renderer`가 font_map 외 폰트를 쓰지 않는지)
- [ ] 폰트가 임베딩되었는가? (`pdftoppm`/`pdffonts`로 확인 가능)
- [ ] 표(table) 노드의 열 폭 합이 페이지 여백을 넘지 않는가?
- [ ] `pdf_reports.file_hash`로 동일 입력 재생성 시 결과 재현성을 추적할 수 있는가?

## 3) ML 결과 검사
- [ ] `ml_classifications.model_version`, `ml_anomalies.model_version`, `ml_forecasts.model_version`이 모두 기록되는가?
- [ ] 계정과목 자동분류 신뢰도가 낮은 건(예: <0.3)은 사람이 검수(override)하도록 안내하는가?
- [ ] 이상거래 탐지는 계정별 표본 수가 `min_samples`(기본 4) 미만이면 스킵되어 오탐이 없는가?

## 4) DART 연동 검사
- [ ] `DART_API_KEY` 부재 시 fixture로 자동 대체되고 `source` 필드로 구분 가능한가?
- [ ] DART 표준계정명이 기업별로 다를 수 있음(예: "매출액" vs "영업수익")을 `mapper.py`의 후보 목록으로 처리하는가?

## 5) 레포 제공 스크립트
- `scripts/demo_generate_reports.py` — Flask/RQ 없이 5종 보고서를 즉시 생성해 스모크 테스트
- `scripts/lint.py` — ruff 정적 분석
- `scripts/test.py` — 전 패키지 pytest 실행

## 6) 2차 확장 검토 항목
- PDF/X 완전 준수(ICC OutputIntent, 트래핑, 오버프린트)는 인쇄 워크플로우와 맞물려 검수 범위가 커질 수 있어 2차 확장으로 권장합니다.
- 표(table) 셀 텍스트 자동 줄바꿈(현재는 미지원)도 2차 확장 포인트입니다.
