from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TerritoryLocalityOut(ORMModel):
    id: UUID
    name: str


class PostcodeDistrictOut(ORMModel):
    id: UUID
    district: str


class TerritoryOut(ORMModel):
    id: UUID
    code: str
    name: str
    description: str | None
    minimum_job_value_gbp: Decimal
    travel_cost_per_km_gbp: Decimal
    base_travel_charge_gbp: Decimal
    is_active: bool
    localities: list[TerritoryLocalityOut] = []
    postcode_districts: list[PostcodeDistrictOut] = []


class TerritoryUpdate(BaseModel):
    minimum_job_value_gbp: Decimal | None = None
    travel_cost_per_km_gbp: Decimal | None = None
    base_travel_charge_gbp: Decimal | None = None
    marketing_budget_monthly_gbp: Decimal | None = None
    is_active: bool | None = None


class TerritoryCreate(BaseModel):
    code: str = Field(..., max_length=10)
    name: str
    description: str | None = None
    minimum_job_value_gbp: Decimal = Decimal("250.00")
    travel_cost_per_km_gbp: Decimal = Decimal("0.45")
    base_travel_charge_gbp: Decimal = Decimal("0.00")


class PostcodeDistrictCreate(BaseModel):
    district: str = Field(..., max_length=8)
    territory_code: str