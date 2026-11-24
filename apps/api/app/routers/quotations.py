import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.quotation import Quotation, QuotationCalculation
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.quotation import (
    InstantQuotationRequest,
    ProvisionalQuotationOut,
    ProvisionalQuotationRequest,
    QuotationOut,
    QuotationSubmitRequest,
)
from app.services.quotation_persist import load_active_service, persist_submitted_quotation
from app.services.quotation_workflow import PROVISIONAL_DISCLAIMER, priced_at_now, price_quotation_inputs

router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.post("/provisional", response_model=ProvisionalQuotationOut)
@limiter.limit("20/minute")
async def calculate_provisional_quotation(
    request: Request,
    body: ProvisionalQuotationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProvisionalQuotationOut:
    """Anonymous pricing only — does not create customers, properties or quotations."""
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
        distance_km_from_base=body.distance_km_from_base,
    )
    out = ProvisionalQuotationOut(
        input_fingerprint=fingerprint,
        priced_at=priced_at_now(),
        covered=territory is not None,
        territory_id=territory.id if territory else None,
        territory_name=territory.name if territory else None,
        surface_supported=supported,
        unsupported_reason=unsupported_reason,
        provisional_disclaimer=PROVISIONAL_DISCLAIMER,
    )
    if pricing is None:
        return out
    out.total_area_sqm = pricing.total_area_sqm
    out.subtotal_ex_vat_gbp = pricing.subtotal_ex_vat_gbp
    out.vat_gbp = pricing.vat_gbp
    out.total_inc_vat_gbp = pricing.total_inc_vat_gbp
    out.estimated_labour_hours = pricing.estimated_labour_hours
    out.meets_minimum_margin = pricing.meets_minimum_margin
    out.requires_approval = pricing.requires_approval
    out.breakdown = pricing.breakdown
    return out


@router.post("/submit", response_model=QuotationOut)
@limiter.limit("12/minute")
async def submit_quotation(
    request: Request,
    body: QuotationSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuotationOut:
    if not body.consent_service_messages:
        raise HTTPException(status_code=400, detail="Service communication consent is required")
    if "@" not in body.email or body.email.endswith("@example.com"):
        raise HTTPException(status_code=400, detail="A valid customer email is required")
    if len(body.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Full name is required")
    if len(body.address_line1.strip()) < 3:
        raise HTTPException(status_code=400, detail="Address line 1 is required")
    return await persist_submitted_quotation(
        db,
        body,
        input_fingerprint=body.input_fingerprint,
        idempotency_key=body.idempotency_key,
    )


@router.post("/instant", response_model=QuotationOut)
@limiter.limit("12/minute")
async def create_instant_quotation(
    request: Request,
    body: InstantQuotationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuotationOut:
    """Legacy endpoint — requires full customer details and a fresh input_fingerprint from /provisional."""
    service = await load_active_service(db, body.service_slug)
    pricing, fingerprint, supported, unsupported_reason, _territory = await price_quotation_inputs(
        db,
        service=service,
        surface_type=body.surface_type,
        surface_condition=body.surface_condition,
        sections_raw=body.sections,
        requires_washing=body.requires_washing,
        customer_washed_already=body.customer_washed_already,
        postcode=body.postcode,
        town=body.town,
        distance_km_from_base=body.distance_km_from_base,
    )
    if not supported:
        raise HTTPException(status_code=400, detail=unsupported_reason or "Surface not supported")
    if pricing is None:
        raise HTTPException(status_code=400, detail="Unable to price quotation")
    return await persist_submitted_quotation(
        db,
        body,
        input_fingerprint=fingerprint,
        idempotency_key=None,
    )


@router.get("", response_model=list[QuotationOut])
async def list_quotations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[QuotationOut]:
    result = await db.execute(
        select(Quotation).options(selectinload(Quotation.sections)).order_by(
            Quotation.created_at.desc()
        ).limit(200)
    )
    return [QuotationOut.model_validate(q) for q in result.scalars().all()]


@router.get("/{quotation_id}", response_model=QuotationOut)
async def get_quotation(
    quotation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuotationOut:
    result = await db.execute(
        select(Quotation)
        .options(selectinload(Quotation.sections))
        .where(Quotation.id == quotation_id)
    )
    q = result.scalar_one_or_none()
    if q is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    calc = await db.execute(
        select(QuotationCalculation)
        .where(QuotationCalculation.quotation_id == quotation_id)
        .order_by(QuotationCalculation.version.desc())
        .limit(1)
    )
    calc_row = calc.scalar_one_or_none()
    out = QuotationOut.model_validate(q)
    if calc_row:
        out.breakdown = json.loads(calc_row.breakdown_json)
    return out