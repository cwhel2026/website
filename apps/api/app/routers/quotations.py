from datetime import UTC, datetime
import json
import secrets
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import Customer, CustomerProperty, Enquiry, PipelineStage
from app.models.quotation import (
    Quotation,
    QuotationCalculation,
    QuotationSection,
    QuotationStatus,
)
from app.models.service import Service
from app.models.user import User
from app.routers.crm import upsert_customer
from app.schemas.quotation import InstantQuotationRequest, QuotationOut
from app.services.pricing_engine import PricingInput, QuotationSectionInput, calculate_quotation
from app.services.territory_lookup import resolve_territory_for_postcode

router = APIRouter(prefix="/quotations", tags=["quotations"])


def _reference() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    suffix = secrets.token_hex(2).upper()
    return f"RMD-{stamp}-{suffix}"


def _section_area(section) -> Decimal:
    if section.area_sqm is not None and section.area_sqm > 0:
        return section.area_sqm
    if section.length_m and section.width_m:
        return section.length_m * section.width_m
    raise HTTPException(status_code=400, detail="Each section needs area or length and width")


@router.post("/instant", response_model=QuotationOut)
async def create_instant_quotation(
    body: InstantQuotationRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> QuotationOut:
    service_result = await db.execute(
        select(Service).where(Service.slug == body.service_slug, Service.is_active.is_(True))
    )
    service = service_result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    territory = await resolve_territory_for_postcode(db, body.postcode, body.town)
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
    prop = CustomerProperty(
        customer_id=customer.id,
        address_line1=body.address_line1,
        address_line2=body.address_line2,
        town=body.town,
        postcode=body.postcode.upper(),
        territory_id=territory.id if territory else None,
    )
    db.add(prop)

    enquiry = Enquiry(
        customer_id=customer.id,
        surface_type=body.surface_type,
        message=body.visible_damage,
        stage=PipelineStage.QUOTE_GENERATED,
    )
    db.add(enquiry)
    await db.flush()

    sections_in = [
        QuotationSectionInput(
            label=s.label,
            length_m=s.length_m,
            width_m=s.width_m,
            area_sqm=_section_area(s),
        )
        for s in body.sections
    ]

    pricing = await calculate_quotation(
        db,
        PricingInput(
            service=service,
            surface_type=body.surface_type,
            surface_condition=body.surface_condition,
            sections=sections_in,
            requires_washing=body.requires_washing,
            customer_washed_already=body.customer_washed_already,
            territory=territory,
            distance_km_from_base=body.distance_km_from_base,
        ),
    )

    status = (
        QuotationStatus.PENDING_APPROVAL
        if pricing.requires_approval
        else QuotationStatus.PROVISIONAL
    )

    quotation = Quotation(
        reference=_reference(),
        customer_id=customer.id,
        enquiry_id=enquiry.id,
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
        estimated_labour_hours=pricing.estimated_labour_hours,
        estimated_materials_gbp=pricing.estimated_materials_gbp,
        estimated_travel_gbp=pricing.estimated_travel_gbp,
        estimated_contribution_gbp=pricing.estimated_contribution_gbp,
        meets_minimum_margin=pricing.meets_minimum_margin,
        requires_approval=pricing.requires_approval,
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