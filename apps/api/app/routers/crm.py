from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.crm import Customer, CustomerProperty, Enquiry, PipelineStage
from app.models.user import User
from app.schemas.crm import CustomerOut, EnquiryCreate, EnquiryOut
from app.services.territory_lookup import resolve_territory_for_postcode

router = APIRouter(prefix="/crm", tags=["crm"])


async def upsert_customer(
    db: AsyncSession, email: str, phone: str | None, full_name: str, **kwargs
) -> Customer:
    result = await db.execute(
        select(Customer).where(func.lower(Customer.email) == email.lower())
    )
    customer = result.scalar_one_or_none()
    if customer:
        customer.full_name = full_name
        if phone:
            customer.phone = phone
        for k, v in kwargs.items():
            if v is not None:
                setattr(customer, k, v)
        return customer
    customer = Customer(email=email, phone=phone, full_name=full_name, **kwargs)
    db.add(customer)
    await db.flush()
    return customer


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
    body: EnquiryCreate, db: Annotated[AsyncSession, Depends(get_db)]
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
    prop_result = await db.execute(
        select(CustomerProperty).where(
            CustomerProperty.customer_id == customer.id,
            func.replace(func.upper(CustomerProperty.postcode), " ", "")
            == body.property.postcode.upper().replace(" ", ""),
        )
    )
    prop = prop_result.scalar_one_or_none()
    if prop is None:
        prop = CustomerProperty(
            customer_id=customer.id,
            territory_id=territory.id if territory else None,
            **body.property.model_dump(),
        )
        db.add(prop)
    enquiry = Enquiry(
        customer_id=customer.id,
        surface_type=body.surface_type,
        message=body.message,
        stage=PipelineStage.NEW_ENQUIRY,
    )
    db.add(enquiry)
    await db.commit()
    await db.refresh(enquiry)
    return enquiry