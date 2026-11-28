import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import Enquiry, PipelineStage
from app.models.quotation import Quotation, QuotationCalculation, QuotationStatus
from app.models.quotation_photo import QuotePhoto, QuotePhotoSet
from app.models.user import User
from app.rate_limit import limiter
from pydantic import BaseModel
from decimal import Decimal
from app.schemas.quotation import (
    InstantQuotationRequest,
    ProvisionalQuotationOut,
    ProvisionalQuotationRequest,
    PublicQuotationOut,
    QuotationSectionOut,
    QuotationOut,
    QuotationSubmitRequest,
)
from app.services.quotation_persist import load_active_service, persist_submitted_quotation
from app.services.quote_conversion import (
    CUSTOMER_HEADING,
    confirmation_steps,
    customer_next_steps,
    follow_up_customer_request,
    validate_conversion_request,
)
from app.services.quotation_workflow import (
    CUSTOMER_NOTE,
    REPAIRS_NOTE,
    customer_package,
    priced_at_now,
    price_quotation_inputs,
)

logger = logging.getLogger(__name__)

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
    try:
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
            pricing_tier=body.pricing_tier,
        )
    except ValueError as exc:
        message = str(exc)
        status = 422 if "not configured" in message else 503
        raise HTTPException(status_code=status, detail=message) from exc
    package = customer_package(
        requires_washing=body.requires_washing,
        customer_washed_already=body.customer_washed_already,
        requires_coating=bool(service.requires_coating),
        service_slug=service.slug,
    )
    out = ProvisionalQuotationOut(
        input_fingerprint=fingerprint,
        priced_at=priced_at_now(),
        covered=territory is not None and pricing is not None,
        territory_name=territory.name if territory else None,
        surface_supported=supported,
        unsupported_reason=unsupported_reason,
        customer_note=package["customer_note"],
        repairs_note=package["repairs_note"],
        included=package["included"],
        visits=package["visits"],
    )
    if pricing is None:
        return out
    out.total_area_sqm = pricing.total_area_sqm
    out.total_gbp = pricing.total_inc_vat_gbp
    out.vat_applied = pricing.vat_charged
    return out


@router.post("/submit", response_model=PublicQuotationOut)
@limiter.limit("12/minute")
async def submit_quotation(
    request: Request,
    body: QuotationSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicQuotationOut:
    validate_conversion_request(body)
    # A quotation request is itself permission to reply about this job.
    # Marketing consent stays optional and is never required.
    body.consent_service_messages = True
    saved, enquiry, _created, photo_token = await persist_submitted_quotation(
        db,
        body,
        input_fingerprint=body.input_fingerprint,
        idempotency_key=body.idempotency_key,
    )
    service = await load_active_service(db, body.service_slug)
    package = customer_package(
        requires_washing=body.requires_washing,
        customer_washed_already=body.customer_washed_already,
        requires_coating=bool(service.requires_coating),
        service_slug=service.slug,
    )
    if enquiry is not None:
        try:
            await follow_up_customer_request(
                db,
                quotation_id=saved.id,
                enquiry=enquiry,
                body=body,
                included=[item["title"] for item in package["included"]],
                two_stage=len(package["visits"]) > 1,
                photo_token=photo_token,
            )
            enquiry = await db.get(Enquiry, enquiry.id)
        except Exception:
            logger.exception("Follow-up after quotation %s failed; enquiry is still saved", saved.reference)
            await db.rollback()
            enquiry = await db.get(Enquiry, enquiry.id)
    email_status = enquiry.email_delivery if enquiry is not None else "not_requested"
    photo_set = await db.scalar(select(QuotePhotoSet).where(QuotePhotoSet.token == photo_token))
    photos_attached = False
    repair_review = False
    if photo_set is not None:
        photo_count = await db.scalar(
            select(func.count()).select_from(QuotePhoto).where(QuotePhoto.set_id == photo_set.id)
        )
        photos_attached = bool(photo_count)
        repair_review = bool(photo_set.review_required)
    return PublicQuotationOut(
        id=saved.id,
        reference=saved.reference,
        status=saved.status,
        surface_type=saved.surface_type,
        surface_condition=saved.surface_condition,
        total_area_sqm=saved.total_area_sqm,
        total_gbp=saved.total_inc_vat_gbp,
        vat_applied=saved.vat_charged,
        customer_note=CUSTOMER_NOTE,
        repairs_note=REPAIRS_NOTE,
        included=package["included"],
        visits=package["visits"],
        created_at=saved.created_at,
        sections=[QuotationSectionOut.model_validate(section) for section in saved.sections],
        intention=enquiry.intention if enquiry and enquiry.intention else body.intention,
        appointment_confirmed=False,
        email_sent=email_status == "sent",
        email_status=email_status,
        telegram_notified=bool(enquiry.telegram_notified) if enquiry is not None else False,
        confirmation_heading=CUSTOMER_HEADING,
        next_steps=customer_next_steps(
            enquiry,
            [],
            email=body.email,
            photos_attached=photos_attached,
            repair_review=repair_review,
        )
        if enquiry is not None
        else "",
        next_step_items=confirmation_steps(enquiry) if enquiry is not None else [],
        suggested_windows=[],
        photos_attached=photos_attached,
        photo_later_path=f"/quote/photos/{photo_token}",
    )


@router.post("/instant", response_model=PublicQuotationOut)
@limiter.limit("4/minute")
async def create_instant_quotation(
    request: Request,
    body: InstantQuotationRequest,
    _: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicQuotationOut:
    """Deprecated for public use — owner-only escape hatch; website must use /provisional then /submit."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is retired for public clients. Use /quotations/provisional then /quotations/submit.",
    )


@router.get("", response_model=list[QuotationOut])
async def list_quotations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[QuotationOut]:
    result = await db.execute(
        select(Quotation)
        .options(selectinload(Quotation.sections), selectinload(Quotation.calculations))
        .order_by(Quotation.created_at.desc())
        .limit(200)
    )
    rows: list[QuotationOut] = []
    for q in result.scalars().all():
        out = QuotationOut.model_validate(q)
        if q.calculations:
            latest = max(q.calculations, key=lambda calc: calc.version)
            out.breakdown = json.loads(latest.breakdown_json)
        rows.append(out)
    return rows


@router.get("/{quotation_id}", response_model=QuotationOut)
async def get_quotation(
    quotation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
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

class AcceptQuotationIn(BaseModel):
    agreed_total_gbp: Decimal
    customer_confirmed: bool


@router.post("/{quotation_id}/accept")
async def accept_quotation(
    quotation_id: UUID,
    body: AcceptQuotationIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    q = await db.get(Quotation, quotation_id, with_for_update=True)
    if q is None:
        raise HTTPException(404, "Quotation not found")
    if q.is_test or q.status in (QuotationStatus.REJECTED, QuotationStatus.EXPIRED):
        raise HTTPException(409, "Quotation cannot be accepted")
    if not body.customer_confirmed or body.agreed_total_gbp != q.total_inc_vat_gbp:
        raise HTTPException(422, "Confirm customer agreement to the exact quotation total")
    if q.requires_approval:
        raise HTTPException(409, "Resolve internal pricing approval first")
    if q.status != QuotationStatus.ACCEPTED:
        q.status = QuotationStatus.ACCEPTED
        if q.enquiry_id:
            enquiry = await db.get(Enquiry, q.enquiry_id)
            if enquiry:
                enquiry.stage = PipelineStage.QUOTE_ACCEPTED
    await db.commit()
    return {"id": str(q.id), "status": q.status.value}
