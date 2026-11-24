from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.marketing import CommercialLead
from app.rate_limit import limiter
from app.services.marketing_intelligence import commercial_lead_score
from app.services.territory_lookup import resolve_territory_for_postcode

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/coverage")
@limiter.limit("60/minute")
async def check_coverage(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    postcode: str = Query(..., min_length=3, max_length=12),
    town: str | None = None,
) -> dict:
    territory = await resolve_territory_for_postcode(db, postcode.upper(), town)
    if territory is None:
        return {
            "covered": False,
            "postcode": postcode.upper(),
            "message": "We could not match this postcode to a current operating territory.",
        }
    return {
        "covered": True,
        "postcode": postcode.upper(),
        "territory_code": territory.code,
        "territory_name": territory.name,
    }


class CommercialEnquiryIn(BaseModel):
    business_name: str
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    address_line1: str | None = None
    town: str | None = None
    postcode: str | None = None
    category: str | None = None
    notes: str = Field(..., min_length=10, max_length=4000)


@router.post("/commercial-enquiry")
@limiter.limit("12/minute")
async def commercial_enquiry(
    request: Request,
    body: CommercialEnquiryIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    territory = None
    if body.postcode:
        territory = await resolve_territory_for_postcode(db, body.postcode.upper(), body.town)
    score = commercial_lead_score(
        has_email=bool(body.contact_email),
        has_postcode=bool(body.postcode),
        category=body.category,
        territory_efficient=territory is not None,
    )
    lead = CommercialLead(
        business_name=body.business_name,
        address_line1=body.address_line1,
        town=body.town,
        postcode=body.postcode.upper() if body.postcode else None,
        territory_id=territory.id if territory else None,
        category=body.category,
        contact_email=str(body.contact_email) if body.contact_email else None,
        contact_phone=body.contact_phone,
        notes=body.notes,
        lead_source="website_commercial",
        score=score,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return {"status": "received", "id": str(lead.id)}