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
    distance_km_from_base: Decimal = Decimal("15")


class QuotationSectionOut(ORMModel):
    id: UUID
    label: str
    length_m: Decimal | None
    width_m: Decimal | None
    area_sqm: Decimal


class QuotationOut(ORMModel):
    id: UUID
    reference: str
    status: QuotationStatus
    surface_type: SurfaceType
    surface_condition: SurfaceCondition
    total_area_sqm: Decimal
    subtotal_ex_vat_gbp: Decimal
    vat_gbp: Decimal
    total_inc_vat_gbp: Decimal
    estimated_labour_hours: Decimal
    estimated_materials_gbp: Decimal
    estimated_travel_gbp: Decimal
    estimated_contribution_gbp: Decimal
    meets_minimum_margin: bool
    requires_approval: bool
    provisional_disclaimer: str
    territory_id: UUID | None
    created_at: datetime
    sections: list[QuotationSectionOut] = []
    breakdown: dict | None = None