"""Persist quotations and related CRM records after pricing validation."""

import json
import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.crm import Enquiry, PipelineStage
from app.models.quotation import (
    Quotation,
    QuotationCalculation,
    QuotationSection,
    QuotationStatus,
)
from app.models.quotation_idempotency import QuotationSubmissionIdempotency
from app.models.service import Service
from app.services.customer_records import ensure_property, upsert_customer
from app.services.geocode import geocode_postcode
from app.schemas.quotation import InstantQuotationRequest, QuotationOut, QuotationSectionIn
from app.services.approval_service import ensure_quotation_approval
from app.services.service_aliases import resolve_service_slug
from app.services.quotation_workflow import (
    PROVISIONAL_DISCLAIMER,
    price_quotation_inputs,
    validate_sections,
)


def _reference() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    suffix = secrets.token_hex(2).upper()
    return f"SC-{stamp}-{suffix}"


async def load_active_service(db: AsyncSession, slug: str) -> Service:
    canonical = resolve_service_slug(slug)
    result = await db.execute(
        select(Service).where(Service.slug == canonical, Service.is_active.is_(True))
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


async def persist_submitted_quotation(
    db: AsyncSession,
    body: InstantQuotationRequest,
    *,
    input_fingerprint: str,
    idempotency_key: str | None,
) -> QuotationOut:
    if idempotency_key:
        existing = await db.execute(
            select(QuotationSubmissionIdempotency).where(
                QuotationSubmissionIdempotency.idempotency_key == idempotency_key
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            result = await db.execute(
                select(Quotation)
                .options(selectinload(Quotation.sections))
                .where(Quotation.id == row.quotation_id)
            )
            q = result.scalar_one_or_none()
            if q:
                out = QuotationOut.model_validate(q)
                calc = await db.execute(
                    select(QuotationCalculation)
                    .where(QuotationCalculation.quotation_id == q.id)
                    .order_by(QuotationCalculation.version.desc())
                    .limit(1)
                )
                calc_row = calc.scalar_one_or_none()
                if calc_row:
                    out.breakdown = json.loads(calc_row.breakdown_json)
                return out

    service = await load_active_service(db, body.service_slug)
    pricing, fingerprint, supported, unsupported_reason, territory = await price_quotation_inputs(
        db,
        service=service,
        surface_type=body.surface_type,
        surface_condition=body.surface_condition,
        sections_raw=body.sections,
        requires_washing=body.requires_washing,
        customer_washed_already=body.customer_washed_already,
        postcode=body.postcode,
        town=body.town,
    )
    if territory is None or pricing is None:
        raise HTTPException(
            status_code=400,
            detail=unsupported_reason or "Location is outside the online service area",
        )
    if fingerprint != input_fingerprint:
        raise HTTPException(
            status_code=409,
            detail="Quotation inputs have changed since the estimate was calculated. Recalculate first.",
        )
    if not supported:
        raise HTTPException(status_code=400, detail=unsupported_reason or "Surface not supported")

    customer = await upsert_customer(
        db,
        email=body.email,
        phone=body.phone,
        full_name=body.full_name,
        consent_marketing=body.consent_marketing,
        consent_service_messages=body.consent_service_messages,
        source=body.source,
        campaign=body.campaign,
    )
    latitude = longitude = None
    try:
        point = await geocode_postcode(body.postcode)
        latitude, longitude = point.latitude, point.longitude
    except HTTPException:
        latitude = longitude = None
    prop = await ensure_property(
        db,
        customer=customer,
        address_line1=body.address_line1,
        address_line2=body.address_line2,
        town=body.town,
        postcode=body.postcode,
        territory_id=territory.id if territory else None,
        latitude=latitude,
        longitude=longitude,
    )

    enquiry = Enquiry(
        customer_id=customer.id,
        property_id=prop.id,
        surface_type=body.surface_type,
        message=body.visible_damage,
        stage=PipelineStage.QUOTE_GENERATED,
        utm_source=body.source,
        utm_campaign=body.campaign,
    )
    db.add(enquiry)
    await db.flush()

    sections_in = validate_sections(body.sections)
    status = (
        QuotationStatus.PENDING_APPROVAL
        if pricing.requires_approval
        else QuotationStatus.PROVISIONAL
    )

    quotation = Quotation(
        reference=_reference(),
        customer_id=customer.id,
        enquiry_id=enquiry.id,
        property_id=prop.id,
        service_id=service.id,
        territory_id=territory.id if territory else None,
        status=status,
        surface_type=body.surface_type,
        surface_condition=body.surface_condition,
        requires_washing=body.requires_washing,
        customer_washed_already=body.customer_washed_already,
        total_area_sqm=pricing.total_area_sqm,
        pricing_profile_id=pricing.pricing_profile_id,
        subtotal_ex_vat_gbp=pricing.subtotal_ex_vat_gbp,
        vat_gbp=pricing.vat_gbp,
        total_inc_vat_gbp=pricing.total_inc_vat_gbp,
        vat_charged=pricing.vat_charged,
        vat_rate_percent=pricing.vat_rate_percent,
        estimated_labour_hours=pricing.estimated_labour_hours,
        estimated_materials_gbp=pricing.estimated_materials_gbp,
        estimated_travel_gbp=pricing.estimated_travel_gbp,
        estimated_contribution_gbp=pricing.estimated_contribution_gbp,
        meets_minimum_margin=pricing.meets_minimum_margin,
        requires_approval=pricing.requires_approval,
        provisional_disclaimer=PROVISIONAL_DISCLAIMER,
    )
    db.add(quotation)
    await db.flush()

    for s, raw in zip(sections_in, body.sections, strict=True):
        db.add(
            QuotationSection(
                quotation_id=quotation.id,
                label=s.label,
                length_m=raw.length_m,
                width_m=raw.width_m,
                area_sqm=s.area_sqm,
            )
        )

    db.add(
        QuotationCalculation(
            quotation_id=quotation.id,
            version=1,
            breakdown_json=json.dumps(pricing.breakdown),
        )
    )
    if idempotency_key:
        db.add(
            QuotationSubmissionIdempotency(
                idempotency_key=idempotency_key,
                quotation_id=quotation.id,
            )
        )
    await ensure_quotation_approval(db, quotation)
    await db.commit()

    result = await db.execute(
        select(Quotation)
        .options(selectinload(Quotation.sections))
        .where(Quotation.id == quotation.id)
    )
    q = result.scalar_one()
    out = QuotationOut.model_validate(q)
    out.breakdown = pricing.breakdown
    return out