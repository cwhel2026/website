from typing import Annotated
from datetime import UTC, datetime

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import Customer, Enquiry, OwnerFollowUp, PipelineStage
from app.models.user import User
from app.schemas.crm import CallbackOutcomeIn, CustomerOut, EnquiryCreate, EnquiryOut
from app.services.customer_records import ensure_property, upsert_customer
from app.services.territory_lookup import resolve_territory_for_postcode

router = APIRouter(prefix="/crm", tags=["crm"])


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[Customer]:
    result = await db.execute(select(Customer).order_by(Customer.created_at.desc()).limit(200))
    return list(result.scalars().all())


@router.get("/enquiries", response_model=list[EnquiryOut])
async def list_enquiries(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[Enquiry]:
    result = await db.execute(select(Enquiry).order_by(Enquiry.created_at.desc()).limit(200))
    return list(result.scalars().all())


@router.post("/enquiries", response_model=EnquiryOut)
async def create_enquiry(
    body: EnquiryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> Enquiry:
    customer = await upsert_customer(
        db,
        email=body.customer.email,
        phone=body.customer.phone,
        full_name=body.customer.full_name,
        consent_marketing=body.customer.consent_marketing,
        consent_service_messages=body.customer.consent_service_messages,
        source=body.customer.source,
        campaign=body.campaign or body.customer.campaign,
    )
    territory = await resolve_territory_for_postcode(
        db, body.property.postcode, body.property.town
    )
    prop = await ensure_property(
        db,
        customer=customer,
        address_line1=body.property.address_line1,
        address_line2=body.property.address_line2,
        town=body.property.town,
        postcode=body.property.postcode,
        territory_id=territory.id if territory else None,
    )
    enquiry = Enquiry(
        customer_id=customer.id,
        property_id=prop.id if prop else None,
        surface_type=body.surface_type,
        message=body.message,
        stage=PipelineStage.NEW_ENQUIRY,
        utm_campaign=body.campaign or body.customer.campaign,
        utm_source=body.customer.source,
    )
    db.add(enquiry)
    await db.commit()
    await db.refresh(enquiry)
    return enquiry


@router.patch("/enquiries/{enquiry_id}/callback", response_model=EnquiryOut)
async def record_callback_outcome(
    enquiry_id: UUID,
    body: CallbackOutcomeIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> Enquiry:
    enquiry = await db.get(Enquiry, enquiry_id, with_for_update=True)
    if enquiry is None or enquiry.intention != "callback_requested":
        raise HTTPException(status_code=404, detail="Callback request not found")
    enquiry.callback_status = "completed" if body.completed else "open"
    enquiry.callback_outcome = body.outcome.strip()
    tasks = (await db.execute(select(OwnerFollowUp).where(OwnerFollowUp.enquiry_id == enquiry.id, OwnerFollowUp.kind == "callback_requested").with_for_update())).scalars().all()
    for task in tasks:
        task.status = "completed" if body.completed else "open"
        task.completed_at = datetime.now(UTC) if body.completed else None
    await db.commit()
    await db.refresh(enquiry)
    return enquiry

@router.get("/follow-ups")
async def list_due_followups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(
        select(OwnerFollowUp, Enquiry, Customer)
        .join(Enquiry, Enquiry.id == OwnerFollowUp.enquiry_id)
        .join(Customer, Customer.id == Enquiry.customer_id)
        .where(OwnerFollowUp.status == "open", Enquiry.is_test.is_(False), Customer.is_test.is_(False))
        .order_by(OwnerFollowUp.due_at.asc().nulls_last())
        .limit(100)
    )
    return [{
        "id": str(task.id), "kind": task.kind, "title": task.title,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "customer_name": customer.full_name,
        "draft": followup_draft(task.kind) if customer.consent_service_messages else None,
        "service_messages_allowed": customer.consent_service_messages,
        "requires_owner_review": True,
    } for task, enquiry, customer in result.all()]


def followup_draft(kind: str) -> str:
    if kind == "ready_to_book":
        return "Thanks for your interest in SurfaceCoat. We'd like to discuss a suitable appointment for your property. No appointment has been reserved yet."
    if kind == "callback_requested":
        return "Thanks for requesting a callback from SurfaceCoat. Please let us know a convenient time to speak."
    return "Thanks for your enquiry with SurfaceCoat. Please let us know if you have any questions about your estimate."
