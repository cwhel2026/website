"""Saved quotation requests against Postgres. No mocked prices, no created bookings."""

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from starlette.testclient import TestClient

from app.models.jobs import AppointmentType
from app.services.scheduling_engine import SlotProposal

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1",
)


def _count(sql: str) -> int:
    url = os.environ["SYNC_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
    engine = sa.create_engine(url)
    with engine.connect() as conn:
        return int(conn.execute(sa.text(sql)).scalar() or 0)


def _payload(fingerprint: str, **extra):
    body = {
        "postcode": "L39 2YG",
        "town": "Ormskirk",
        "service_slug": "tarmac-driveway-restoration",
        "surface_type": "tarmac",
        "surface_condition": "fair",
        "requires_washing": True,
        "customer_washed_already": False,
        "sections": [{"label": "Drive", "length_m": 10, "width_m": 4, "area_sqm": 40}],
        "full_name": "Test Customer",
        "address_line1": "1 Test Lane",
        "consent_marketing": False,
        "consent_service_messages": False,
        "input_fingerprint": fingerprint,
        "source": "website",
        "campaign": "spring-test",
    }
    body.update(extra)
    return body


@requires_postgres
def test_three_actions_save_intent_without_booking_or_fake_email(monkeypatch):
    from app.main import app

    async def _fixed_travel(_db, _postcode: str) -> Decimal:
        return Decimal("22.5")

    class _Point:
        latitude = 53.566
        longitude = -2.885

    async def _geo(_postcode: str):
        return _Point()

    async def _windows(*_args, **_kwargs):
        start = datetime.now(UTC) + timedelta(days=3)
        prep = SlotProposal(
            start=start,
            end=start + timedelta(hours=2),
            appointment_type=AppointmentType.PREPARATION,
            travel_minutes=25,
            weather_score=80,
            weather_safe=True,
        )
        return [prep], []

    monkeypatch.setattr("app.services.quotation_workflow.travel_km_from_base", _fixed_travel)
    monkeypatch.setattr("app.services.quotation_persist.geocode_postcode", _geo)
    monkeypatch.setattr("app.services.quote_conversion.propose_two_stage_slots", _windows)

    jobs_before = _count("SELECT COUNT(*) FROM jobs")
    appointments_before = _count("SELECT COUNT(*) FROM appointments")

    with TestClient(app) as client:
        provisional = client.post(
            "/api/v1/quotations/provisional",
            json={
                "postcode": "L39 2YG",
                "town": "Ormskirk",
                "service_slug": "tarmac-driveway-restoration",
                "surface_type": "tarmac",
                "sections": [{"label": "Drive", "length_m": 10, "width_m": 4, "area_sqm": 40}],
            },
        )
        assert provisional.status_code == 200, provisional.text
        fingerprint = provisional.json()["input_fingerprint"]

        booked = client.post(
            "/api/v1/quotations/submit",
            json=_payload(
                fingerprint,
                email="book.conversion@example.co.uk",
                phone="07123456789",
                intention="ready_to_book",
                idempotency_key="conversion-book-1",
            ),
        )
        assert booked.status_code == 200, booked.text
        booked_body = booked.json()
        assert booked_body["appointment_confirmed"] is False
        assert booked_body["email_sent"] is False
        assert booked_body["telegram_notified"] is False
        assert booked_body["intention"] == "ready_to_book"
        assert "not a confirmed booking" in booked_body["next_steps"]
        assert booked_body["suggested_windows"]
        assert "breakdown" not in booked_body
        assert "vat_gbp" not in booked_body

        again = client.post(
            "/api/v1/quotations/submit",
            json=_payload(
                fingerprint,
                email="book.conversion@example.co.uk",
                phone="07123456789",
                intention="ready_to_book",
                idempotency_key="conversion-book-1",
            ),
        )
        assert again.status_code == 200, again.text
        assert again.json()["reference"] == booked_body["reference"]

        callback = client.post(
            "/api/v1/quotations/submit",
            json=_payload(
                fingerprint,
                email="callback.conversion@example.co.uk",
                phone="07123456780",
                intention="callback_requested",
                callback_preferred_time="Weekday mornings",
                idempotency_key="conversion-callback-1",
            ),
        )
        assert callback.status_code == 200, callback.text
        assert "Weekday mornings" in callback.json()["next_steps"]
        assert callback.json()["appointment_confirmed"] is False

        missing_time = client.post(
            "/api/v1/quotations/submit",
            json=_payload(
                fingerprint,
                email="callback2.conversion@example.co.uk",
                phone="07123456780",
                intention="callback_requested",
                idempotency_key="conversion-callback-missing",
            ),
        )
        assert missing_time.status_code == 400

        emailed = client.post(
            "/api/v1/quotations/submit",
            json=_payload(
                fingerprint,
                email="estimate.conversion@example.co.uk",
                intention="estimate_requested",
                idempotency_key="conversion-email-1",
            ),
        )
        assert emailed.status_code == 200, emailed.text
        email_body = emailed.json()
        assert email_body["email_sent"] is False
        assert email_body["email_status"] == "not_sent_smtp_unconfigured"
        assert "We have emailed" not in email_body["next_steps"]
        assert "could not email" in email_body["next_steps"]
        assert email_body["appointment_confirmed"] is False

    assert _count("SELECT COUNT(*) FROM jobs") == jobs_before
    assert _count("SELECT COUNT(*) FROM appointments") == appointments_before
    assert _count("SELECT COUNT(*) FROM enquiries WHERE utm_campaign = 'spring-test'") == 3
    assert _count(
        "SELECT COUNT(*) FROM enquiries WHERE intention = 'ready_to_book' AND priority = 'high' AND utm_campaign = 'spring-test'"
    ) == 1
    assert _count(
        "SELECT COUNT(*) FROM enquiries WHERE intention = 'callback_requested' AND callback_status = 'open' AND utm_campaign = 'spring-test'"
    ) == 1
    assert _count(
        "SELECT COUNT(*) FROM customers WHERE email = 'estimate.conversion@example.co.uk' AND consent_marketing = false"
    ) == 1
