"""Shared quotation validation, fingerprinting and pricing assembly."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service, SurfaceType
from app.services.vat_settings import vat_position_on
from app.schemas.quotation import QuotationSectionIn
from app.services.pricing_engine import PricingInput, QuotationSectionInput, calculate_quotation
from app.services.quotation_travel import travel_km_from_base
from app.services.territory_lookup import resolve_territory_for_postcode

CUSTOMER_NOTE = (
    "This estimate is for the work described below. "
    "We confirm the final price after checking the measurements on site."
)
REPAIRS_NOTE = (
    "Additional repairs are not included. Any repair work is agreed with you separately before we carry it out."
)
PROVISIONAL_DISCLAIMER = CUSTOMER_NOTE


def section_area(section: QuotationSectionIn) -> Decimal:
    if section.area_sqm is not None and section.area_sqm > 0:
        return section.area_sqm
    if section.length_m and section.width_m and section.length_m > 0 and section.width_m > 0:
        return section.length_m * section.width_m
    raise HTTPException(
        status_code=400,
        detail=f"Section '{section.label}' needs area (m²) or length and width in metres",
    )


def validate_sections(sections: list[QuotationSectionIn]) -> list[QuotationSectionInput]:
    if not sections:
        raise HTTPException(status_code=400, detail="At least one measurement section is required")
    out: list[QuotationSectionInput] = []
    total = Decimal("0")
    for raw in sections:
        area = section_area(raw)
        if area < Decimal("1"):
            raise HTTPException(status_code=400, detail="Each section must be at least 1 m²")
        if area > Decimal("2500"):
            raise HTTPException(status_code=400, detail="Section area exceeds online limit — contact us")
        total += area
        out.append(
            QuotationSectionInput(
                label=raw.label or "Main area",
                length_m=raw.length_m,
                width_m=raw.width_m,
                area_sqm=area,
            )
        )
    if total > Decimal("5000"):
        raise HTTPException(status_code=400, detail="Total area exceeds online limit — use commercial enquiry")
    return out


def surface_supported(service: Service, surface_type: SurfaceType) -> tuple[bool, str | None]:
    allowed = {s.strip() for s in service.surface_types.split(",") if s.strip()}
    if surface_type.value in allowed or SurfaceType.OTHER.value in allowed:
        return True, None
    return False, f"Surface '{surface_type.value}' is not supported for service '{service.slug}'"


def pricing_payload_dict(
    *,
    service_slug: str,
    surface_type: str,
    surface_condition: str,
    requires_washing: bool,
    customer_washed_already: bool,
    postcode: str,
    town: str | None,
    sections: list[dict[str, Any]],
    distance_km_from_base: str | float,
    pricing_tier: str = "launch",
) -> dict[str, Any]:
    return {
        "service_slug": service_slug,
        "surface_type": surface_type,
        "surface_condition": surface_condition,
        "requires_washing": requires_washing,
        "customer_washed_already": customer_washed_already,
        "postcode": postcode.strip().upper(),
        "town": (town or "").strip(),
        "sections": sections,
        "distance_km_from_base": str(distance_km_from_base),
        "pricing_tier": pricing_tier,
    }


def quotation_input_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def customer_package(
    *,
    requires_washing: bool,
    customer_washed_already: bool,
    requires_coating: bool,
) -> dict[str, Any]:
    """What the customer is buying. No prices, rates or internal rules."""
    washing_visit = requires_washing and not customer_washed_already
    coating_visit = requires_coating
    included: list[dict[str, str]] = []
    visits: list[dict[str, str]] = []
    if washing_visit:
        included.append(
            {
                "title": "Professional driveway cleaning",
                "detail": "We clean the surface before any restoration work.",
            }
        )
        included.append(
            {
                "title": "Surface preparation",
                "detail": "We prepare the surface so the coating can bond.",
            }
        )
    if coating_visit:
        included.append(
            {
                "title": "Specialist restoration coating",
                "detail": "Applied once the surface is dry and the weather is suitable.",
            }
        )
    if not washing_visit and not coating_visit:
        included.append(
            {
                "title": "The agreed restoration work",
                "detail": "We complete the selected service in a single visit.",
            }
        )
    included.append(
        {
            "title": "All materials and labour",
            "detail": "Materials and labour for the work above are included in this estimate.",
        }
    )
    if washing_visit and coating_visit:
        visits = [
            {"title": "Visit 1 — Cleaning and preparation", "detail": "We clean and prepare the surface."},
            {
                "title": "Visit 2 — Restoration coating",
                "detail": "We apply the specialist restoration coating once the surface is dry and the weather is suitable.",
            },
        ]
    elif coating_visit:
        visits = [
            {
                "title": "One visit — Restoration coating",
                "detail": "We apply the specialist restoration coating once the surface is dry and the weather is suitable.",
            }
        ]
    elif washing_visit:
        visits = [
            {"title": "One visit — Cleaning and preparation", "detail": "We clean and prepare the surface."}
        ]
    else:
        visits = [
            {"title": "One visit", "detail": "We complete the agreed work in a single visit."}
        ]
    return {
        "included": included,
        "visits": visits,
        "repairs_note": REPAIRS_NOTE,
        "customer_note": CUSTOMER_NOTE,
    }


async def price_quotation_inputs(
    db: AsyncSession,
    *,
    service: Service,
    surface_type: SurfaceType,
    surface_condition,
    sections_raw: list[QuotationSectionIn],
    requires_washing: bool,
    customer_washed_already: bool,
    postcode: str,
    town: str | None,
    pricing_tier: str = "launch",
) -> tuple[Any, str, bool, str | None, Any]:
    supported, unsupported_reason = surface_supported(service, surface_type)
    sections_in = validate_sections(sections_raw)
    territory = await resolve_territory_for_postcode(db, postcode, town or "")
    distance_km_from_base = await travel_km_from_base(db, postcode)
    section_dicts = [
        {
            "label": s.label,
            "length_m": str(s.length_m) if s.length_m is not None else None,
            "width_m": str(s.width_m) if s.width_m is not None else None,
            "area_sqm": str(s.area_sqm),
        }
        for s, raw in zip(sections_in, sections_raw, strict=True)
    ]
    fingerprint_basis = pricing_payload_dict(
        service_slug=service.slug,
        surface_type=surface_type.value,
        surface_condition=surface_condition.value
        if hasattr(surface_condition, "value")
        else str(surface_condition),
        requires_washing=requires_washing,
        customer_washed_already=customer_washed_already,
        postcode=postcode,
        town=town,
        sections=section_dicts,
        distance_km_from_base=distance_km_from_base,
        pricing_tier=pricing_tier,
    )
    fingerprint = quotation_input_fingerprint(fingerprint_basis)
    if territory is None:
        unsupported_reason = (
            unsupported_reason or "We do not currently offer online booking for this location."
        )
        return None, fingerprint, supported, unsupported_reason, None
    if not supported:
        return None, fingerprint, False, unsupported_reason, territory

    charge_vat, vat_rate, _percent = await vat_position_on(db, datetime.now(UTC).date())
    pricing = await calculate_quotation(
        db,
        PricingInput(
            service=service,
            surface_type=surface_type,
            surface_condition=surface_condition,
            sections=sections_in,
            requires_washing=requires_washing,
            customer_washed_already=customer_washed_already,
            territory=territory,
            distance_km_from_base=distance_km_from_base,
            pricing_tier=pricing_tier,
            charge_vat=charge_vat,
            vat_rate=vat_rate,
        ),
    )
    return pricing, fingerprint, True, unsupported_reason, territory


def priced_at_now() -> datetime:
    return datetime.now(UTC)