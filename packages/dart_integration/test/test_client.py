import os

import pytest

from dart_integration.client import fetch_financial_statements, search_corp_code


def test_search_corp_code_uses_fixture_when_no_key(monkeypatch):
    monkeypatch.delenv("DART_API_KEY", raising=False)
    result = search_corp_code("삼성전자")
    assert result["source"] == "fixture"
    assert any(m["corp_code"] == "00126380" for m in result["matches"])


def test_fetch_financial_statements_uses_fixture_when_no_key(monkeypatch):
    monkeypatch.delenv("DART_API_KEY", raising=False)
    result = fetch_financial_statements("00126380", "2023")
    assert result["source"] == "fixture"
    assert any(item["account_nm"] == "자산총계" for item in result["items"])


@pytest.mark.skipif(not os.environ.get("DART_API_KEY"), reason="DART_API_KEY 미설정 - 라이브 API 테스트 건너뜀")
def test_search_corp_code_live_finds_samsung():
    result = search_corp_code("삼성전자")
    assert result["source"] == "live"
    assert any(m["corp_code"] == "00126380" for m in result["matches"])


@pytest.mark.skipif(not os.environ.get("DART_API_KEY"), reason="DART_API_KEY 미설정 - 라이브 API 테스트 건너뜀")
def test_fetch_financial_statements_live():
    result = fetch_financial_statements("00126380", "2023")
    assert result["source"] == "live"
    assert any(item["account_nm"] == "자산총계" for item in result["items"])
