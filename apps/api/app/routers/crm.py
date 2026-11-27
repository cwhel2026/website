from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import Customer, Enquiry, PipelineStage
from app.models.user import User
from app.schemas.crm import CustomerOut, EnquiryCreate, EnquiryOut
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