"""Public provisional quote — real pricing engine, no mocked totals."""

import os
from decimal import Decimal

import pytest
from starlette.testclient import TestClient

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1",
)


@requires_postgres
def test_provisional_quote_returns_computed_price(monkeypatch):
    from app.main import app
    async def _fixed_travel(_db, _postcode: str) -> Decimal:
        return Decimal("22.5")

    monkeypatch.setattr("app.services.quotation_workflow.travel_km_from_base", _fixed_travel)

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/quotations/provisional",
            json={
                "postcode": "L39 2JG",
                "town": "Ormskirk",
                "service_slug": "tarmac-restoration",
                "surface_type": "tarmac",
                "surface_condition": "fair",
                "requires_washing": True,
                "customer_washed_already": False,
                "sections": [{"label": "Drive", "length_m": 10, "width_m": 4, "area_sqm": 40}],
            },
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["surface_supported"] is True
        assert body["vat_applied"] is False
        total = Decimal(body["total_gbp"])
        assert total > 0
        assert total % Decimal("5") == 0
        assert "breakdown" not in body
        assert "subtotal_ex_vat_gbp" not in body
        assert "vat_gbp" not in body
        joined = " ".join(item["title"] for item in body["included"] + body["visits"])
        assert "Professional driveway cleaning" in joined
        assert "Visit 2" in joined
        assert "£" not in str(body["included"])
        assert "live pricing" not in body["customer_note"].lower()
        assert body.get("input_fingerprint")

        standard = client.post(
            "/api/v1/quotations/provisional",
            json={
                "postcode": "L39 2JG",
                "town": "Ormskirk",
                "service_slug": "tarmac-driveway-restoration",
                "surface_type": "tarmac",
                "surface_condition": "good",
                "pricing_tier": "standard",
                "requires_washing": False,
                "customer_washed_already": True,
                "sections": [{"label": "Drive", "length_m": 10, "width_m": 4, "area_sqm": 40}],
            },
        )
        assert standard.status_code == 200, standard.text
        assert standard.json()["vat_applied"] is False
        assert "breakdown" not in standard.json()
        assert Decimal(standard.json()["total_gbp"]) % Decimal("5") == 0
        assert "One visit" in " ".join(item["title"] for item in standard.json()["visits"])

        blocked = client.post(
            "/api/v1/quotations/provisional",
            json={
                "postcode": "L39 2JG",
                "town": "Ormskirk",
                "service_slug": "tarmac-driveway-restoration",
                "surface_type": "block_paving",
                "sections": [{"label": "Drive", "area_sqm": 40}],
            },
        )
        assert blocked.status_code == 422
        assert "not configured" in blocked.json()["detail"]