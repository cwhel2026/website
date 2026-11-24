from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.crm import PipelineStage
from app.models.service import SurfaceType
from app.schemas.common import ORMModel


class CustomerCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    full_name: str
    consent_marketing: bool = False
    consent_service_messages: bool = True
    source: str | None = None
    campaign: str | None = None


class CustomerPropertyCreate(BaseModel):
    address_line1: str
    address_line2: str | None = None
    town: str
    postcode: str


class CustomerOut(ORMModel):
    id: UUID
    email: EmailStr
    phone: str | None
    full_name: str
    source: str | None
    campaign: str | None
    created_at: datetime


class EnquiryCreate(BaseModel):
    customer: CustomerCreate
    property: CustomerPropertyCreate
    surface_type: SurfaceType | None = None
    message: str | None = None
    campaign: str | None = None


class EnquiryOut(ORMModel):
    id: UUID
    customer_id: UUID
    stage: PipelineStage
    surface_type: SurfaceType | None
    message: str | None
    created_at: datetime