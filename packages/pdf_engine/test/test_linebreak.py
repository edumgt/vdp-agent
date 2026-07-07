from pdf_engine.linebreak import line_break


def test_space_based_wraps():
    lines = line_break("Hello world this is a long sentence", 100, "space_based", 16)
    assert len(lines) >= 2


def test_cjk_wraps():
    lines = line_break("가나다라마바사아자차카타파하", 60, "cjk", 16)
    assert len(lines) >= 2


def test_empty_text_returns_single_blank_line():
    assert line_break("", 100, "space_based", 12) == [""]
