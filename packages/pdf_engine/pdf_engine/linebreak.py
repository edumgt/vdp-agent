"""
표/텍스트 셀 줄바꿈 유틸.
- space_based: 공백 단어 단위 줄바꿈(영/숫자 등)
- cjk: 문자 단위 줄바꿈(한/중/일)
실제 인쇄 품질을 위해서는 폰트 메트릭 기반 폭 측정이 필요하나,
MVP는 문자 종류별 em 비율로 근사합니다.
"""
import re

_ALNUM = re.compile(r"[A-Za-z0-9]")


def _estimate_width(text: str, font_size: float) -> float:
    w = 0.0
    for ch in text:
        if ch == " ":
            w += font_size * 0.35
        elif _ALNUM.match(ch):
            w += font_size * 0.55
        else:
            w += font_size * 0.60  # accents/CJK 등
    return w


def line_break(text: str, max_width: float, policy: str = "space_based", font_size: float = 12) -> list[str]:
    s = text or ""
    if not s.strip():
        return [""]

    if policy == "cjk":
        out = []
        line = ""
        for ch in s:
            nxt = line + ch
            if _estimate_width(nxt, font_size) > max_width and len(line) > 0:
                out.append(line)
                line = ch
            else:
                line = nxt
        if line:
            out.append(line)
        return out

    # space_based (기본): 공백을 보존하며 토큰 단위로 분리
    tokens = re.split(r"(\s+)", s)
    out = []
    line = ""
    for token in tokens:
        nxt = line + token
        if _estimate_width(nxt, font_size) > max_width and line.strip():
            out.append(line.rstrip())
            line = token.lstrip()
        else:
            line = nxt
    if line:
        out.append(line.rstrip())
    return out
