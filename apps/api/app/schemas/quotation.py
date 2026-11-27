from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.quotation import QuotationStatus, SurfaceCondition
from app.models.service import SurfaceType
from app.schemas.common import ORMModel


class QuotationSectionIn(BaseModel):
    label: str = "Main area"
    length_m: Decimal | None = None
    width_m: Decimal | None = None
    area_sqm: Decimal | None = None


class ProvisionalQuotationRequest(BaseModel):
    """Anonymous price calculation — no customer or CRM records."""

    postcode: str
    town: str | None = None
    service_slug: str
    surface_type: SurfaceType
    surface_condition: SurfaceCondition = SurfaceCondition.FAIR
    sections: list[QuotationSectionIn] = Field(..., min_length=1)
    requires_washing: bool = True
    customer_washed_already: bool = False
    pricing_tier: str = "launch"


class ProvisionalQuotationOut(BaseModel):
    input_fingerprint: str
    priced_at: datetime
    covered: bool
    territory_name: str | None = None
    surface_supported: bool
    unsupported_reason: str | None = None
    total_area_sqm: Decimal | None = None
    subtotal_ex_vat_gbp: Decimal | None = None
    vat_gbp: Decimal | None = None
    total_inc_vat_gbp: Decimal | None = None
    provisional_disclaimer: str
    breakdown: dict | None = None


class AdminProvisionalQuotationOut(ProvisionalQuotationOut):
    territory_id: UUID | None = None
    estimated_labour_hours: Decimal | None = None
    meets_minimum_margin: bool | None = None
    requires_approval: bool | None = None
    internal_breakdown: dict | None = None


class InstantQuotationRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    address_line1: str
    address_line2: str | None = None
    town: str
    postcode: str
    service_slug: str
    surface_type: SurfaceType
    surface_condition: SurfaceCondition = SurfaceCondition.FAIR
    sections: list[QuotationSectionIn] = Field(..., min_length=1)
    requires_washing: bool = True
    customer_washed_already: bool = False
    visible_damage: str | None = None
    access_restrictions: str | None = None
    water_available: bool = True
    consent_service_messages: bool = True
    consent_marketing: bool = False
    source: str | None = "website"
    campaign: str | None = None


class QuotationSubmitRequest(InstantQuotationRequest):
    """Persist quotation and CRM records with genuine customer details."""

    input_fingerprint: str = Field(..., min_length=64, max_length=64)
    idempotency_key: str | None = Field(default=None, max_length=64)


class QuotationSectionOut(ORMModel):
    id: UUID
    label: str
    length_m: Decimal | None
    width_m: Decimal | None
    area_sqm: Decimal


class PublicQuotationOut(ORMModel):
    id: UUID
    reference: str
    status: QuotationStatus
    surface_type: SurfaceType
    surface_condition: SurfaceCondition
    total_area_sqm: Decimal
    subtotal_ex_vat_gbp: Decimal
    vat_gbp: Decimal
    total_inc_vat_gbp: Decimal
    provisional_disclaimer: str
    created_at: datetime
    sections: list[QuotationSectionOut] = []
    breakdown: dict | None = None


class QuotationOut(PublicQuotationOut):
    """Owner dashboard — includes internal costing fields."""

    estimated_labour_hours: Decimal
    estimated_materials_gbp: Decimal
    estimated_travel_gbp: Decimal
    estimated_contribution_gbp: Decimal
    meets_minimum_margin: bool
    requires_approval: bool
    territory_id: UUID | None