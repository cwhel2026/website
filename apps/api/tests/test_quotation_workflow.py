from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.service import SurfaceType
from app.schemas.quotation import QuotationSectionIn
from app.services.quotation_workflow import (
    pricing_payload_dict,
    public_pricing_breakdown,
    quotation_input_fingerprint,
    validate_sections,
)


def test_validate_sections_requires_area():
    with pytest.raises(HTTPException) as exc:
        validate_sections([QuotationSectionIn(label="Main", length_m=None, width_m=None)])
    assert exc.value.status_code == 400


def test_fingerprint_changes_when_measurements_change():
    base = pricing_payload_dict(
        service_slug="tarmac-restoration",
        surface_type=SurfaceType.TARMAC.value,
        surface_condition="fair",
        requires_washing=True,
        customer_washed_already=False,
        postcode="L39 2JG",
        town="Ormskirk",
        sections=[{"label": "Main", "length_m": "10", "width_m": "4", "area_sqm": "40"}],
        distance_km_from_base="15",
    )
    changed = dict(base)
    changed["sections"] = [
        {"label": "Main", "length_m": "12", "width_m": "4", "area_sqm": "48"},
    ]
    assert quotation_input_fingerprint(base) != quotation_input_fingerprint(changed)


def test_public_breakdown_strips_internal_costs():
    internal = {
        "profile_id": "abc",
        "lines": [
            {"label": "Surface restoration", "amount_gbp": 720.0},
            {"label": "Travel", "amount_gbp": 40.0},
        ],
        "costs": {"labour_gbp": 200.0, "materials_gbp": 80.0},
        "margin_ratio": 0.42,
    }
    public = public_pricing_breakdown(internal)
    assert public is not None
    assert "costs" not in public
    assert "margin_ratio" not in public
    assert len(public["lines"]) == 2


def test_section_area_from_length_width():
    sections = validate_sections(
        [QuotationSectionIn(label="Main", length_m=Decimal("10"), width_m=Decimal("4"))]
    )
    assert sections[0].area_sqm == Decimal("40")