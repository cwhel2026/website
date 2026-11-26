from io import BytesIO

import pytest
from PIL import Image

from app.services.marketing.image_compositor import FORMATS, render_before_after
from app.services.marketing.launch_readiness import assess_launch_readiness
from app.services.marketing.media_store import store_bytes
from app.services.marketing.prospect_categories import vertical_places_queries


def test_launch_readiness_pre_launch():
    data = assess_launch_readiness()
    assert data["pre_launch"] is True
    assert data["can_use_offline_features"] is True
    assert "items" in data


def test_vertical_queries():
    q = vertical_places_queries("supermarket", "Preston")
    assert any("Preston" in s for s in q)


def test_compositor_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETING_MEDIA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    img = Image.new("RGB", (800, 600), color=(80, 80, 80))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    before_key, _ = store_bytes(data=buf.getvalue(), filename="before.jpg", subdir="jobs")
    img2 = Image.new("RGB", (800, 600), color=(40, 100, 40))
    buf2 = BytesIO()
    img2.save(buf2, format="JPEG")
    after_key, _ = store_bytes(data=buf2.getvalue(), filename="after.jpg", subdir="jobs")
    for fmt in list(FORMATS.keys())[:1]:
        key, data = render_before_after(before_key=before_key, after_key=after_key, format_name=fmt)
        assert len(data) > 1000
        assert key