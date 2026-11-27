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
        assert body["total_inc_vat_gbp"] is not None
        total = Decimal(body["total_inc_vat_gbp"])
        assert total > 0
        assert total % Decimal("5") == 0
        assert Decimal(body["subtotal_ex_vat_gbp"]) + Decimal(body["vat_gbp"]) == total
        surface = next(line for line in body["breakdown"]["lines"] if line["label"] == "Surface restoration")
        assert Decimal(str(surface["amount_gbp"])) == Decimal("400.00")
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
        standard_surface = next(
            line
            for line in standard.json()["breakdown"]["lines"]
            if line["label"] == "Surface restoration"
        )
        assert Decimal(str(standard_surface["amount_gbp"])) == Decimal("480.00")

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