"""Photograph preparation and assessment never change a quotation price."""

import pytest

from app.services.quote_photo_ai import assess_image_bytes, interpret_findings
from app.services.quote_photo_store import prepare_image
from app.services.quote_photos import record_repair_decision


def _jpeg_with_private_note() -> bytes:
    from PIL import Image
    import io

    image = Image.new("RGB", (40, 30), (90, 70, 50))
    raw = io.BytesIO()
    image.save(raw, format="JPEG", quality=90)
    data = raw.getvalue()
    comment = b"SECRET-GPS-NOTE"
    marker = b"\xff\xfe" + (len(comment) + 2).to_bytes(2, "big") + comment
    return data[:2] + marker + data[2:]


def test_prepare_image_stays_within_the_upload_target_and_keeps_detail():
    from PIL import Image
    import io

    from app.services.quote_photo_store import DETAIL_FLOOR_EDGE, TARGET_MAX_BYTES

    image = Image.new("RGB", (2400, 1600), (180, 170, 150))
    for x in range(200, 2200):
        image.putpixel((x, 800), (20, 20, 20))
    raw = io.BytesIO()
    image.save(raw, format="JPEG", quality=95)
    cleaned = prepare_image(raw.getvalue())
    assert len(cleaned) <= TARGET_MAX_BYTES
    opened = Image.open(io.BytesIO(cleaned))
    assert max(opened.size) >= DETAIL_FLOOR_EDGE


def test_prepare_image_strips_metadata_and_rejects_other_files():
    cleaned = prepare_image(_jpeg_with_private_note())
    assert cleaned.startswith(b"\xff\xd8")
    assert b"SECRET-GPS-NOTE" not in cleaned
    try:
        prepare_image(b"this is not a photograph")
    except ValueError:
        return
    raise AssertionError("non-image uploads must be rejected")


def test_minor_wear_does_not_require_review_or_a_price():
    result = interpret_findings([{"kind": "normal_wear", "note": "fading"}, {"kind": "edge_wear", "note": "edge"}])
    assert result["review_required"] is False
    assert result["changes_price"] is False
    assert "does not add a charge" in result["summary"]
    assert "£" not in result["summary"]


def test_significant_damage_is_flagged_without_a_price():
    result = interpret_findings([{"kind": "crack", "note": "across the bay"}, {"kind": "price", "note": "ignore"}])
    assert result["review_required"] is True
    assert result["changes_price"] is False
    assert "structural condition" in result["summary"]
    assert all(item["kind"] != "price" for item in result["findings"])


@pytest.mark.asyncio
async def test_missing_provider_does_not_invent_an_assessment(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "app.services.quote_photo_ai.get_settings",
        lambda: SimpleNamespace(openai_api_key=None, openai_model="gpt-4o-mini"),
    )
    result = await assess_image_bytes(b"\xff\xd8\xff")
    assert result["status"] == "unavailable"
    assert result["changes_price"] is False
    assert result["review_required"] is False


def test_assessment_enqueue_survives_a_missing_worker(monkeypatch):
    from uuid import uuid4

    def _boom(*_args, **_kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr("app.worker.tasks.assess_quote_photos.apply_async", _boom)
    from app.services.quote_photos import _publish_photo_assessment

    _publish_photo_assessment(str(uuid4()))


def test_repair_decision_does_not_touch_the_quotation_total():
    class _Set:
        repair_price_gbp = None
        repair_note = None
        review_status = "open"

    class _Quote:
        total_inc_vat_gbp = "675.00"

    photo_set = _Set()
    quotation = _Quote()
    before = quotation.total_inc_vat_gbp
    record_repair_decision(photo_set, repair_price_gbp=40, repair_note="Fill the crack", approved=True)
    assert quotation.total_inc_vat_gbp == before
    assert photo_set.review_status == "approved"
    assert photo_set.repair_price_gbp == 40
