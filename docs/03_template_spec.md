# 렌더트리(문서 템플릿) JSON 규격 (v2.0)

`accounting_engine`의 모든 빌더(`build_balance_sheet`, `build_general_ledger`, `build_closing_report` 등)는
아래와 동일한 형태의 **렌더트리**를 반환하며, `pdf_engine.render_pdf(render_tree, font_map, out_path)` 하나로 모든 문서를 렌더링합니다.

- 좌표 단위: pt(72pt = 1 inch), 좌하단 원점(ReportLab 기본 좌표계와 동일)
- 페이지 크기: 8.5 x 11 inch (612 x 792 pt), Bleed 기본 9pt
- `y` 값은 "상단 기준 오프셋"으로 다루며(box.y = bleed + node.y가 상단), 텍스트/표는 위→아래로 그려집니다.

---

## 1) 최상위 구조
```json
{
  "pages": [
    { "page": { "width_pt": 612, "height_pt": 792, "bleed_pt": 9 }, "nodes": [ /* ... */ ] }
  ]
}
```

## 2) 노드 타입

### text
```json
{
  "type": "text",
  "x": 72, "y": 700, "w": 468, "h": 30,
  "style": { "font_key": "body", "font_size": 16, "align": "left", "leading": 20 },
  "text": "재무상태표 (기준일: 2026-06-30)"
}
```
- `lines`(list[str])를 직접 넘기면 자동 줄바꿈을 건너뜁니다(이미 계산된 라인).
- `align`: left | center | right

### table
```json
{
  "type": "table",
  "x": 72, "y": 680,
  "col_widths": [50, 300, 118], "row_height": 16,
  "header": ["코드", "계정과목", "금액"],
  "rows": [["101", "현금", "1,000,000"]],
  "style": { "font_key": "body", "font_size": 9, "header_font_size": 9 }
}
```
- 헤더 유무는 선택(없으면 `header` 생략).
- 셀 텍스트는 폭에 맞춰 줄바꿈되지 않으므로(MVP), 열 폭을 충분히 확보하거나 내용을 축약합니다.

### bar_chart
```json
{
  "type": "bar_chart",
  "x": 72, "y": 680, "w": 468, "h": 220,
  "categories": ["2026-01", "2026-02"], "values": [1000000, 1500000],
  "title": "월별 매출 추이",
  "style": { "font_key": "body" }
}
```
- 단순 사각형 막대 + 축 라벨(MVP). 범례/복수 시리즈는 2차 확장 포인트.

---

## 3) 폰트 매핑(font_map)
```json
{ "body": "NotoSansKR-Regular.ttf" }
```
- `FONTS_DIR`(기본 `./assets/fonts`) 기준 상대 파일명. 레포에는 폰트 바이너리를 포함하지 않습니다(`04_font_policy.md`).

---

## 4) 색상
현재 텍스트는 흑백(black)만 지원합니다(MVP). CMYK/브랜드 컬러 등은 2차 확장 포인트로, `style.color`에
`{"mode":"cmyk","c":0,"m":0,"y":0,"k":100}` 형태를 추가해 `pdf_engine.renderer._resolve_color`를 확장하면 됩니다.

## 5) 보고서 유형별 빌더 매핑
| report_type | 빌더 함수 | 페이지 구성 |
|---|---|---|
| financial_statement | `build_financial_statement_report` | 재무상태표(1p) + 손익계산서(1p) |
| ledger | `build_journal_register` + `build_general_ledger` | 분개장(N p) + 계정별 원장(계정 수 만큼) |
| tax_summary | `build_tax_summary` | 매입/매출 정리표(1p) |
| closing_report | `build_closing_report` | KPI+ML 요약(1p) + 월별 추이 차트(1p) |
| company_dashboard | `build_company_dashboard` | 대시보드 요약(1p) + 제조원가명세서(1p) + 유형자산목록(1p) |
| dart_replica | `dart_integration.build_dart_replica_render_tree` | 재무상태표 원본(1p) + 손익계산서+비율(1p) |
