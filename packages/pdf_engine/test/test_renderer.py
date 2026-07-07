import glob
import os
import shutil
import tempfile

import pytest

from pdf_engine.renderer import render_pdf

_CANDIDATE_FONTS = [
    os.environ.get("TEST_FONT_PATH", ""),
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _find_test_font():
    for path in _CANDIDATE_FONTS:
        if path and os.path.exists(path):
            return path
    matches = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
    return matches[0] if matches else None


@pytest.fixture()
def fonts_dir():
    font_path = _find_test_font()
    if not font_path:
        pytest.skip("검증용 TTF 폰트를 찾을 수 없어 renderer 테스트를 건너뜁니다 (레포 정책상 폰트 미포함).")
    tmp_dir = tempfile.mkdtemp()
    shutil.copy(font_path, os.path.join(tmp_dir, "test-font.ttf"))
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_render_pdf_multi_page_with_table_and_chart(fonts_dir, tmp_path):
    render_tree = {
        "pages": [
            {
                "page": {"width_pt": 612, "height_pt": 792, "bleed_pt": 9},
                "nodes": [
                    {
                        "type": "text",
                        "x": 72, "y": 700, "w": 400, "h": 40,
                        "style": {"font_key": "body", "font_size": 18, "align": "left"},
                        "text": "재무상태표",
                    },
                    {
                        "type": "table",
                        "x": 72, "y": 640, "col_widths": [200, 120, 120], "row_height": 20,
                        "header": ["계정과목", "당기", "전기"],
                        "rows": [["현금", "1,000,000", "800,000"], ["보통예금", "5,000,000", "4,200,000"]],
                        "style": {"font_key": "body", "font_size": 10},
                    },
                ],
            },
            {
                "page": {"width_pt": 612, "height_pt": 792, "bleed_pt": 9},
                "nodes": [
                    {
                        "type": "bar_chart",
                        "x": 72, "y": 700, "w": 300, "h": 150,
                        "categories": ["1월", "2월", "3월"],
                        "values": [100, 150, 90],
                        "title": "월별 매출 추이",
                        "style": {"font_key": "body"},
                    }
                ],
            },
        ]
    }

    out_path = str(tmp_path / "out.pdf")
    result = render_pdf(render_tree, {"body": "test-font.ttf"}, out_path, fonts_dir=fonts_dir)

    assert result["pages"] == 2
    assert os.path.exists(out_path)
    assert result["size"] > 0
    with open(out_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"
