import pytest

from app.services.marketing.integration_setup import build_integration_centre
from app.services.marketing.media_store import store_bytes, resolve_path
from app.services.marketing.research.osm_overpass import query_commercial_features


def test_integration_centre_lists_providers():
    data = build_integration_centre()
    platforms = {i["platform"] for i in data["integrations"]}
    assert "companies_house" in platforms
    assert "google_places" in platforms
    assert "meta_ads" in platforms


def test_media_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETING_MEDIA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    key, digest = store_bytes(data=b"hello", filename="test.jpg")
    assert digest
    path = resolve_path(key)
    assert path.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_osm_overpass_returns_structure():
    result = await query_commercial_features(lat=53.75, lon=-2.7, radius_m=2000)
    assert "ok" in result
    assert "items" in result