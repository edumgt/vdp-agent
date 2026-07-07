"""
PDF Engine (ReportLab 기반)
- render_tree(JSON 직렬화 가능한 dict) -> 인쇄용 PDF
- 폰트 임베딩: TTF/OTF를 pdfmetrics.registerFont로 풀 임베딩
- Bleed/Trim: bleed_pt 만큼 페이지를 확장해 생성(트림 박스는 문서화된 여백으로 관리)
- 완전한 PDF/X 준수(ICC OutputIntent, 오버프린트/트래핑)는 2차 확장 포인트입니다.
"""
import hashlib
import os

from reportlab.lib.colors import CMYKColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .linebreak import line_break


def _env(name, fallback=None):
    return os.environ.get(name, fallback)


def _resolve_font_path(fonts_dir: str, file_name: str) -> str:
    p = os.path.join(fonts_dir, file_name)
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"Font file not found: {p}. assets/fonts 에 TTF/OTF를 배치하고 font_map을 갱신하세요."
        )
    return p


def _register_fonts(fonts_dir: str, font_map: dict) -> dict:
    """font_key -> file name 매핑을 등록하고, {font_key: registered_name} 반환."""
    registry = {}
    for font_key, file_name in font_map.items():
        path = _resolve_font_path(fonts_dir, file_name)
        pdfmetrics.registerFont(TTFont(font_key, path))
        registry[font_key] = font_key
    return registry


def _resolve_color(style: dict):
    color = (style or {}).get("color")
    if not color:
        return black
    if color.get("mode") == "cmyk":
        return CMYKColor(
            color.get("c", 0) / 100.0,
            color.get("m", 0) / 100.0,
            color.get("y", 0) / 100.0,
            color.get("k", 0) / 100.0,
        )
    return black


def _draw_text_node(c: canvas.Canvas, node: dict, bleed: float, default_font: str):
    style = node.get("style") or {}
    font_key = style.get("font_key", default_font)
    font_size = style.get("font_size", 12)
    leading = style.get("leading", font_size * 1.2)
    align = style.get("align", "left")
    color = _resolve_color(style)

    x = bleed + node["x"]
    y_top = bleed + node["y"]
    w = node.get("w", 0)

    lines = node.get("lines")
    if lines is None:
        lines = line_break(node.get("text", ""), w, style.get("policy", "space_based"), font_size)

    c.setFont(font_key, font_size)
    c.setFillColor(color)

    cursor_y = y_top
    for line in lines:
        if align == "center":
            text_w = c.stringWidth(line, font_key, font_size)
            draw_x = x + max(0, (w - text_w) / 2)
        elif align == "right":
            text_w = c.stringWidth(line, font_key, font_size)
            draw_x = x + max(0, w - text_w)
        else:
            draw_x = x
        c.drawString(draw_x, cursor_y, line)
        cursor_y -= leading


def _draw_table_node(c: canvas.Canvas, node: dict, bleed: float, default_font: str):
    style = node.get("style") or {}
    font_key = style.get("font_key", default_font)
    font_size = style.get("font_size", 10)
    header_font_size = style.get("header_font_size", font_size)
    row_height = node.get("row_height", font_size * 1.8)
    col_widths = node["col_widths"]
    header = node.get("header") or []
    rows = node.get("rows") or []

    x0 = bleed + node["x"]
    y0 = bleed + node["y"]  # top-left of table
    total_w = sum(col_widths)

    all_rows = ([header] if header else []) + rows
    n_rows = len(all_rows)

    # 격자선
    c.setLineWidth(0.75)
    c.setStrokeColor(black)
    for i in range(n_rows + 1):
        y = y0 - i * row_height
        c.line(x0, y, x0 + total_w, y)
    cx = x0
    for w in col_widths:
        c.line(cx, y0, cx, y0 - n_rows * row_height)
        cx += w
    c.line(cx, y0, cx, y0 - n_rows * row_height)

    # 셀 텍스트
    pad = 4
    for r_idx, row in enumerate(all_rows):
        is_header = header and r_idx == 0
        size = header_font_size if is_header else font_size
        c.setFont(font_key, size)
        c.setFillColor(black)
        cx = x0
        row_top = y0 - r_idx * row_height
        text_y = row_top - row_height + pad + (row_height - size) / 2.5
        for c_idx, cell in enumerate(row):
            c.drawString(cx + pad, text_y, str(cell))
            cx += col_widths[c_idx]


def _draw_bar_chart_node(c: canvas.Canvas, node: dict, bleed: float, default_font: str):
    style = node.get("style") or {}
    font_key = style.get("font_key", default_font)
    x0 = bleed + node["x"]
    y0 = bleed + node["y"]  # top of chart bounding box
    w = node["w"]
    h = node["h"]
    categories = node.get("categories", [])
    values = node.get("values", [])
    title = node.get("title")

    baseline_y = y0 - h
    c.setFont(font_key, 9)
    c.setFillColor(black)
    if title:
        c.drawString(x0, y0 + 4, title)

    c.setLineWidth(1)
    c.line(x0, baseline_y, x0 + w, baseline_y)  # x축

    if not values:
        return
    max_val = max(max(values, default=0), 1)
    n = len(values)
    gap = w / n
    bar_w = gap * 0.6
    for i, val in enumerate(values):
        bar_h = (val / max_val) * (h - 14) if max_val else 0
        bx = x0 + i * gap + (gap - bar_w) / 2
        c.rect(bx, baseline_y, bar_w, bar_h, fill=1, stroke=0)
        c.setFont(font_key, 7)
        label = str(categories[i]) if i < len(categories) else ""
        c.drawCentredString(bx + bar_w / 2, baseline_y - 10, label)


_NODE_DRAWERS = {
    "text": _draw_text_node,
    "table": _draw_table_node,
    "bar_chart": _draw_bar_chart_node,
}


def render_pdf(render_tree: dict, font_map: dict, out_path: str, fonts_dir: str | None = None) -> dict:
    """
    render_tree: {"pages": [{"page": {width_pt,height_pt,bleed_pt}, "nodes": [...]}]}
    font_map: {"latin_sans": "NotoSansKR-Regular.ttf", ...}
    """
    fonts_dir = fonts_dir or _env("FONTS_DIR", "./assets/fonts")
    registry = _register_fonts(fonts_dir, font_map)
    default_font = next(iter(registry.values()), "Helvetica")

    pages = render_tree["pages"]
    first_page = pages[0]["page"]
    bleed0 = first_page.get("bleed_pt", 0)
    c = canvas.Canvas(out_path, pagesize=(first_page["width_pt"] + bleed0 * 2, first_page["height_pt"] + bleed0 * 2))

    for page_tree in pages:
        page = page_tree["page"]
        bleed = page.get("bleed_pt", 0)
        page_w = page["width_pt"] + bleed * 2
        page_h = page["height_pt"] + bleed * 2
        c.setPageSize((page_w, page_h))

        c.setFillColor(white)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        for node in page_tree.get("nodes", []):
            drawer = _NODE_DRAWERS.get(node.get("type"))
            if drawer:
                drawer(c, node, bleed, default_font)

        c.showPage()

    c.save()

    with open(out_path, "rb") as f:
        data = f.read()
    file_hash = hashlib.sha256(data).hexdigest()
    return {"out_path": out_path, "size": len(data), "file_hash": file_hash, "pages": len(pages)}
