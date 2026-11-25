from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.company import OnboardingTaskStatus, PayrollStatus, VatStatus


class CompanyProfileIn(BaseModel):
    registered_name: str | None = None
    companies_house_number: str | None = Field(default=None, max_length=16)
    incorporation_date: date | None = None
    trading_start_date: date | None = None
    registered_office: str | None = None
    accounting_reference_month: int | None = Field(default=None, ge=1, le=12)
    accounting_reference_day: int | None = Field(default=None, ge=1, le=31)
    company_utr: str | None = None
    vat_status: VatStatus = VatStatus.UNKNOWN
    vat_number: str | None = None
    paye_status: PayrollStatus = PayrollStatus.UNKNOWN
    paye_reference: str | None = None
    corporation_tax_registered: bool | None = None
    accountant_name: str | None = None
    accountant_email: EmailStr | None = None
    mettle_account_hint: str | None = None
    freeagent_configured: bool = False
    directors_json: dict | None = None
    shareholders_json: dict | None = None
    notes: str | None = None


class OnboardingTaskOut(BaseModel):
    slug: str
    title: str
    plain_language: str
    status: OnboardingTaskStatus
    due_date: date | None
    evidence_note: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class CompanyProfileOut(CompanyProfileIn):
    id: UUID
    onboarding_completed_at: datetime | None
    tasks: list[OnboardingTaskOut] = []

    model_config = {"from_attributes": True}


class CompanyOnboardingSummary(BaseModel):
    profile: CompanyProfileOut
    completion_pct: int
    next_actions: list[str]