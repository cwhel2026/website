"""Shared quotation validation, fingerprinting and pricing assembly."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service, SurfaceType
from app.schemas.quotation import QuotationSectionIn
from app.services.pricing_engine import PricingInput, QuotationSectionInput, calculate_quotation
from app.services.quotation_travel import travel_km_from_base
from app.services.territory_lookup import resolve_territory_for_postcode

PROVISIONAL_DISCLAIMER = (
    "This is a provisional online estimate from your live pricing rules. "
    "Final pricing is confirmed after measurement verification and site inspection. "
    "Complex surfaces, access limits or weather may adjust scope."
)


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
    }


def quotation_input_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def public_pricing_breakdown(breakdown: dict | None) -> dict | None:
    if not breakdown:
        return None
    lines = []
    for line in breakdown.get("lines") or []:
        if line.get("amount_gbp") is not None:
            lines.append({"label": line["label"], "amount_gbp": line["amount_gbp"]})
    return {"lines": lines} if lines else None


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
    )
    fingerprint = quotation_input_fingerprint(fingerprint_basis)
    if territory is None:
        unsupported_reason = (
            unsupported_reason or "We do not currently offer online booking for this location."
        )
        return None, fingerprint, supported, unsupported_reason, None
    if not supported:
        return None, fingerprint, False, unsupported_reason, territory

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
        ),
    )
    return pricing, fingerprint, True, unsupported_reason, territory


def priced_at_now() -> datetime:
    return datetime.now(UTC)