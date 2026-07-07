# 폰트 정책 / 임베딩 가이드 (v2.0)

## 1) 원칙
- 재무제표/원장 등 인쇄·법적 보관용 문서에서 **대체 폰트 치환**이 발생하면 안 됩니다.
- `pdf_engine`은 `reportlab.pdfbase.pdfmetrics.registerFont`로 TTF/OTF를 **풀 임베딩**합니다.
- 폰트 라이선스(임베딩 허용 여부)를 반드시 확인합니다.

## 2) 레포에 폰트 바이너리를 포함하지 않는 이유
- 상용 폰트/라이선스 이슈 방지
- 프로젝트별 폰트 선정(브랜드/한글 지원 여부)에 따라 폰트가 달라질 수 있음

## 3) 폰트 배치 위치
- 폰트 파일은 `.env`의 `FONTS_DIR` 경로로 지정합니다.
- 기본값: `./assets/fonts`
- 한글 지원이 필요하므로 Noto Sans KR, 나눔고딕 등 한글 글리프를 포함한 TTF를 권장합니다.

예)
- assets/fonts/NotoSansKR-Regular.ttf

## 4) font_map 설정
`accounting_engine`이 생성하는 렌더트리의 `style.font_key`(기본 `"body"`)와
`apps/worker`의 `FONT_FILE` 환경변수(기본 `NotoSansKR-Regular.ttf`)가 매핑되어 `pdf_engine.render_pdf`에 전달됩니다.
여러 서체(굵게/보통)가 필요하면 `worker_jobs/jobs.py`의 `_font_map()`을 확장해 `font_key`별 파일을 추가하세요.

## 5) 로컬 검증 방법
레포 정책상 폰트를 커밋하지 않으므로, 개발 중에는 시스템에 설치된 TTF(예: Ubuntu의 `/usr/share/fonts/truetype/nanum/NanumGothic.ttf`)를
`assets/fonts/`에 복사해 임시로 사용할 수 있습니다(커밋 금지, `.gitignore`에 이미 제외 처리됨).
