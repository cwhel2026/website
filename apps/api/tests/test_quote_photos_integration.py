"""Photograph upload against Postgres. The provisional price does not wait on or change for AI."""

import io
import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from PIL import Image
from starlette.testclient import TestClient

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1",
)


def _count(sql: str) -> int:
    url = os.environ["SYNC_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
    engine = sa.create_engine(url)
    with engine.connect() as conn:
        return int(conn.execute(sa.text(sql)).scalar() or 0)


def _jpeg() -> bytes:
    raw = io.BytesIO()
    Image.new("RGB", (24, 16), (30, 30, 30)).save(raw, format="JPEG")
    return raw.getvalue()


@requires_postgres
def test_photos_attach_without_changing_the_estimate(monkeypatch, tmp_path):
    from app.main import app

    monkeypatch.setenv("QUOTE_PHOTOS_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()

    async def _fixed_travel(_db, _postcode: str) -> Decimal:
        return Decimal("22.5")

    class _Point:
        latitude = 53.566
        longitude = -2.885

    async def _geo(_postcode: str):
        return _Point()

    async def _vision(_data: bytes) -> dict:
        return {
            "status": "assessed",
            "findings": [{"kind": "crack", "note": "a line in the bay"}],
            "review_required": True,
            "summary": "Flagged for review. The estimate is unchanged.",
            "changes_price": False,
        }

    monkeypatch.setattr("app.services.quotation_workflow.travel_km_from_base", _fixed_travel)
    monkeypatch.setattr("app.services.quotation_persist.geocode_postcode", _geo)
    queued: list[str] = []

    def _queue(set_id) -> None:
        queued.append(str(set_id))

    monkeypatch.setattr("app.routers.quotation_photos.enqueue_photo_assessment", _queue)
    monkeypatch.setattr("app.services.quote_photos.assess_image_bytes", _vision)

    jobs_before = _count("SELECT COUNT(*) FROM jobs")
    price_body = {
        "postcode": "L39 2YG",
        "town": "Ormskirk",
        "service_slug": "tarmac-driveway-restoration",
        "surface_type": "tarmac",
        "sections": [{"label": "Drive", "length_m": 10, "width_m": 4, "area_sqm": 40}],
    }

    with TestClient(app) as client:
        first = client.post("/api/v1/quotations/provisional", json=price_body)
        assert first.status_code == 200, first.text
        total = first.json()["total_gbp"]

        rejected = client.post(
            "/api/v1/quotation-photos",
            files={"files": ("notes.txt", b"not a photo", "text/plain")},
        )
        assert rejected.status_code == 400

        uploaded = client.post(
            "/api/v1/quotation-photos",
            data={"note": "Crack near the gate"},
            files={"files": ("drive.jpg", _jpeg(), "image/jpeg")},
        )
        assert uploaded.status_code == 200, uploaded.text
        token = uploaded.json()["token"]
        photo_id = uploaded.json()["photos"][0]["id"]
        assert "review_required" not in uploaded.json()

        second = client.post("/api/v1/quotations/provisional", json=price_body)
        assert second.status_code == 200, second.text
        assert second.json()["total_gbp"] == total

        listed = client.get(f"/api/v1/quotation-photos/{token}")
        assert listed.status_code == 200
        image = client.get(f"/api/v1/quotation-photos/{token}/{photo_id}")
        assert image.status_code == 200
        assert image.headers["content-type"].startswith("image/jpeg")
        assert client.get(f"/api/v1/quotation-photos/not-a-real-token/{photo_id}").status_code == 404

        submitted = client.post(
            "/api/v1/quotations/submit",
            json={
                **price_body,
                "full_name": "Photo Customer",
                "email": "photo.integration@example.co.uk",
                "phone": "07123456789",
                "address_line1": "1 Test Lane",
                "consent_marketing": False,
                "intention": "ready_to_book",
                "input_fingerprint": first.json()["input_fingerprint"],
                "idempotency_key": f"photo-upload-{token[:12]}",
                "photo_token": token,
                "photo_note": "Crack near the gate",
            },
        )
        assert submitted.status_code == 200, submitted.text
        body = submitted.json()
        assert Decimal(str(body["total_gbp"])) == Decimal(str(total))
        assert body["photos_attached"] is True
        assert body["photo_later_path"] == f"/quote/photos/{token}"
        assert "booking request" in body["next_steps"].lower()
        assert body["appointment_confirmed"] is False
        assert "breakdown" not in body

    assert _count("SELECT COUNT(*) FROM jobs") == jobs_before
    url = os.environ["SYNC_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
    sync_engine = sa.create_engine(url)
    with sync_engine.connect() as conn:
        row = conn.execute(
            sa.text(
                "SELECT marketing_use_allowed, quotation_id IS NOT NULL, customer_id IS NOT NULL, "
                "property_id IS NOT NULL, enquiry_id IS NOT NULL, review_required, ai_status "
                "FROM quote_photo_sets WHERE token = :token"
            ),
            {"token": token},
        ).one()
    assert row[0] is False
    assert row[1] is True
    assert row[2] is True
    assert row[3] is True
    assert row[4] is True
    assert row[5] is False
    assert row[6] == "pending"
    assert queued

    import asyncio
    from uuid import UUID

    from app.database import engine as async_engine
    from app.services.quote_photos import assess_photo_set

    async def _run_worker() -> None:
        await async_engine.dispose()
        await assess_photo_set(UUID(queued[0]))

    asyncio.run(_run_worker())
    with sync_engine.connect() as conn:
        after = conn.execute(
            sa.text(
                "SELECT review_required, ai_status, "
                "(SELECT total_inc_vat_gbp FROM quotations WHERE id = quote_photo_sets.quotation_id) "
                "FROM quote_photo_sets WHERE token = :token"
            ),
            {"token": token},
        ).one()
    assert after[0] is True
    assert after[1] == "assessed"
    assert Decimal(str(after[2])) == Decimal(str(total))
    get_settings.cache_clear()
