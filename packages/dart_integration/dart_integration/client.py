"""
OpenDART(전자공시시스템) Open API 클라이언트.
- DART_API_KEY(crtfc_key)가 설정되어 있으면 실제 API를 호출합니다.
- 키가 없으면 fixtures/(실제 공개 데이터로 채운 샘플)를 사용해 동일 인터페이스로 동작합니다.
  (fixtures/fnltt_sample.json은 삼성전자의 실제 공개 재무제표 응답을 축약한 것입니다.)
"""
import io
import json
import os
import time
import zipfile
import xml.etree.ElementTree as ET
from importlib import resources

import requests

CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
FNLTT_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"


class DartApiError(Exception):
    pass


def _cache_dir() -> str:
    d = os.environ.get("DART_CACHE_DIR", os.path.join(os.getcwd(), ".cache", "dart"))
    os.makedirs(d, exist_ok=True)
    return d


def _load_fixture_corpcode_bytes() -> bytes:
    with resources.files("dart_integration").joinpath("fixtures", "corpcode_sample.xml").open("rb") as f:
        return f.read()


def _load_fixture_fnltt() -> dict:
    with resources.files("dart_integration").joinpath("fixtures", "fnltt_sample.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_corp_code_xml(api_key: str | None, cache_ttl_seconds: int = 86400) -> tuple[bytes, str]:
    if not api_key:
        return _load_fixture_corpcode_bytes(), "fixture"

    cache_path = os.path.join(_cache_dir(), "CORPCODE.xml")
    if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path)) < cache_ttl_seconds:
        with open(cache_path, "rb") as f:
            return f.read(), "live"

    resp = requests.get(CORP_CODE_URL, params={"crtfc_key": api_key}, timeout=30)
    resp.raise_for_status()

    if not zipfile.is_zipfile(io.BytesIO(resp.content)):
        # 인증 실패 등의 오류는 zip이 아닌 XML 오류 메시지로 반환됨
        raise DartApiError(resp.text)

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        data = zf.read("CORPCODE.xml")

    with open(cache_path, "wb") as f:
        f.write(data)
    return data, "live"


def _parse_corp_code_xml(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    out = []
    for item in root.findall("list"):
        out.append({
            "corp_code": (item.findtext("corp_code") or "").strip(),
            "corp_name": (item.findtext("corp_name") or "").strip(),
            "stock_code": (item.findtext("stock_code") or "").strip(),
            "modify_date": (item.findtext("modify_date") or "").strip(),
        })
    return out


def search_corp_code(name: str, api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get("DART_API_KEY")
    xml_bytes, source = _fetch_corp_code_xml(api_key)
    all_corps = _parse_corp_code_xml(xml_bytes)
    matches = [c for c in all_corps if name in c["corp_name"]]
    return {"source": source, "matches": matches}


def fetch_financial_statements(
    corp_code: str, bsns_year: str, reprt_code: str = "11011", fs_div: str = "CFS", api_key: str | None = None
) -> dict:
    api_key = api_key or os.environ.get("DART_API_KEY")
    if not api_key:
        data = _load_fixture_fnltt()
        return {"source": "fixture", "items": data["list"]}

    resp = requests.get(
        FNLTT_URL,
        params={"crtfc_key": api_key, "corp_code": corp_code, "bsns_year": bsns_year, "reprt_code": reprt_code, "fs_div": fs_div},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "000":
        raise DartApiError(f"{payload.get('status')}: {payload.get('message')}")
    return {"source": "live", "items": payload.get("list", [])}
