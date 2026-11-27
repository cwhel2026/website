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


class PackageItem(BaseModel):
    title: str
    detail: str


class ProvisionalQuotationOut(BaseModel):
    """Public price. No internal rates, travel, VAT splits or rounding lines."""

    input_fingerprint: str
    priced_at: datetime
    covered: bool
    territory_name: str | None = None
    surface_supported: bool
    unsupported_reason: str | None = None
    total_area_sqm: Decimal | None = None
    total_gbp: Decimal | None = None
    vat_applied: bool = False
    included: list[PackageItem] = []
    visits: list[PackageItem] = []
    repairs_note: str
    customer_note: str


class AdminProvisionalQuotationOut(ProvisionalQuotationOut):
    territory_id: UUID | None = None
    estimated_labour_hours: Decimal | None = None
    meets_minimum_margin: bool | None = None
    requires_approval: bool | None = None
    subtotal_ex_vat_gbp: Decimal | None = None
    vat_gbp: Decimal | None = None
    internal_breakdown: dict | None = None


class InstantQuotationRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    address_line1: str
    address_line2: str | None = None
    town: str | None = None
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
    intention: str = "estimate_requested"
    callback_preferred_time: str | None = None
    photo_token: str | None = None
    photo_note: str | None = Field(default=None, max_length=1000)


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


class SuggestedWindowOut(BaseModel):
    label: str
    starts: datetime
    kind: str


class PublicQuotationOut(ORMModel):
    id: UUID
    reference: str
    status: QuotationStatus
    surface_type: SurfaceType
    surface_condition: SurfaceCondition
    total_area_sqm: Decimal
    total_gbp: Decimal
    vat_applied: bool
    customer_note: str
    repairs_note: str
    included: list[PackageItem] = []
    visits: list[PackageItem] = []
    created_at: datetime
    sections: list[QuotationSectionOut] = []
    intention: str = "estimate_requested"
    appointment_confirmed: bool = False
    email_sent: bool = False
    email_status: str = "not_requested"
    telegram_notified: bool = False
    next_steps: str = ""
    suggested_windows: list[SuggestedWindowOut] = []
    photos_attached: bool = False
    photo_later_path: str = ""


class QuotationOut(ORMModel):
    """Owner dashboard — full costing. Not returned by the public quote endpoints."""

    id: UUID
    reference: str
    status: QuotationStatus
    surface_type: SurfaceType
    surface_condition: SurfaceCondition
    total_area_sqm: Decimal
    subtotal_ex_vat_gbp: Decimal
    vat_gbp: Decimal
    total_inc_vat_gbp: Decimal
    vat_charged: bool = False
    vat_rate_percent: Decimal = Decimal("0")
    provisional_disclaimer: str
    created_at: datetime
    sections: list[QuotationSectionOut] = []
    breakdown: dict | None = None
    estimated_labour_hours: Decimal
    estimated_materials_gbp: Decimal
    estimated_travel_gbp: Decimal
    estimated_contribution_gbp: Decimal
    meets_minimum_margin: bool
    requires_approval: bool
    territory_id: UUID | None