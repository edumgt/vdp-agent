# 문서 개요
- 작성일: 2026-07-07 (v2.0 — 법인 기장 PDF 생성 모듈로 전면 개편)
- 본 폴더는 법인 기장(회계) PDF 생성 모듈 구축에 필요한 **요구사항/아키텍처/규격/API/운영/ML** 문서를 포함합니다.

목차:
1. `01_requirements.md` — 범위/수용 기준
2. `02_architecture.md` — 시스템 구성 및 워크플로우(mermaid)
3. `03_template_spec.md` — 렌더트리(문서 템플릿) JSON 스키마/예시
4. `04_font_policy.md` — 폰트 임베딩 정책/라이선스 가이드
5. `05_api_spec.md` — API 명세
6. `06_preflight_checklist.md` — 산출물(재무 PDF) 검증 체크리스트
7. `07_deploy_guide.md` — Docker 기반 배포/운영 가이드
8. `08_techstack_workflow.md` — 기술스택, E2E 워크플로우, **도입 ML/DL 알고리즘 상세**

## v1 → v2 변경 요약
- 도메인: 다국어 개인화 동화책(VDP) → **법인 기장(회계) PDF 생성**
- 언어/스택: Node.js/Express/React → **Python(Flask/RQ) + Vanilla JS**
- 신규 ML/DL: 증빙 OCR+정보추출(EasyOCR), 계정과목 자동분류(TF-IDF+Naive Bayes), 이상거래 탐지(IsolationForest), 현금흐름·매출 예측(Holt 지수평활)
- 신규 연동: OpenDART(전자공시시스템) 회사검색 + 재무제표 수집 + 자체 템플릿 재현
- 신규 산출물: 제조원가명세서, 유형자산 목록, 수출비중을 포함한 기업 대시보드
