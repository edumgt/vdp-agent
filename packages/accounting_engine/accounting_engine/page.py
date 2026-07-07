"""페이지/렌더트리 공통 상수 및 헬퍼 (A4가 아닌 8.5x11in/pt 기준, 기존 template_spec과 동일)."""

PAGE_WIDTH_PT = 612
PAGE_HEIGHT_PT = 792
BLEED_PT = 9
MARGIN_PT = 72
CONTENT_WIDTH_PT = PAGE_WIDTH_PT - MARGIN_PT * 2  # 468


def new_page(nodes: list) -> dict:
    return {
        "page": {"width_pt": PAGE_WIDTH_PT, "height_pt": PAGE_HEIGHT_PT, "bleed_pt": BLEED_PT},
        "nodes": nodes,
    }


def title_node(text: str, y: float = 700, font_size: float = 20) -> dict:
    return {
        "type": "text",
        "x": MARGIN_PT, "y": y, "w": CONTENT_WIDTH_PT, "h": 30,
        "style": {"font_key": "body", "font_size": font_size, "align": "left"},
        "text": text,
    }


def paragraph_node(text: str, y: float, font_size: float = 11) -> dict:
    return {
        "type": "text",
        "x": MARGIN_PT, "y": y, "w": CONTENT_WIDTH_PT, "h": 60,
        "style": {"font_key": "body", "font_size": font_size, "align": "left", "leading": font_size * 1.5},
        "text": text,
    }
