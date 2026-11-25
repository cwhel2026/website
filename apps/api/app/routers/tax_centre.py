from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.compliance.engine import refresh_compliance_calendar, upcoming_reminders
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.personal_tax import dividend_tax, income_tax_on_non_dividend_income
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES
from app.services.tax_engine.vat_monitor import rolling_vat_taxable_turnover

router = APIRouter(prefix="/finance/tax-centre", tags=["tax-centre"])


@router.get("/rules")
async def tax_rule_pack(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return {
        "version": ACTIVE_RULES.version,
        "effective_from": ACTIVE_RULES.effective_from,
        "sources": ACTIVE_RULES.sources,
        "notes": ACTIVE_RULES.notes,
    }


@router.get("/corporation-tax")
async def ct_estimate(
    _: Annotated[User, Depends(get_current_admin)],
    profit_gbp: float = 0,
) -> dict:
    return corporation_tax_with_marginal_relief(Decimal(str(profit_gbp)))


@router.get("/personal-income-tax")
async def personal_income_tax(
    _: Annotated[User, Depends(get_current_admin)],
    taxable_gbp: float = 0,
) -> dict:
    return income_tax_on_non_dividend_income(Decimal(str(taxable_gbp)))


@router.get("/dividend-tax")
async def personal_dividend_tax(
    _: Annotated[User, Depends(get_current_admin)],
    dividend_gbp: float = 0,
    other_income_gbp: float = 0,
) -> dict:
    return dividend_tax(
        Decimal(str(dividend_gbp)),
        other_non_dividend_gbp=Decimal(str(other_income_gbp)),
    )


@router.get("/vat-monitor")
async def vat_monitor(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await rolling_vat_taxable_turnover(db)


@router.get("/reserves")
async def tax_reserves(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await compute_tax_reserves(db)
    await db.commit()
    return result


@router.get("/compliance")
async def compliance_calendar(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    within_days: int = 90,
) -> dict:
    await refresh_compliance_calendar(db)
    reminders = await upcoming_reminders(db, within_days=within_days)
    await db.commit()
    return {"within_days": within_days, "obligations": reminders}