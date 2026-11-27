"""Company VAT registration. Quotations store the decision made on the day they are priced."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile, VatStatus

STANDARD_VAT_PERCENT = Decimal("20")


def vat_applies(
    status: VatStatus | None,
    effective_from: date | None,
    on: date,
    rate_percent: Decimal | None,
) -> tuple[bool, Decimal]:
    """Return (charge_vat, rate as a fraction). Unregistered and future dates charge nothing."""
    if status != VatStatus.REGISTERED:
        return False, Decimal("0")
    if effective_from is not None and on < effective_from:
        return False, Decimal("0")
    percent = rate_percent if rate_percent is not None and rate_percent > 0 else STANDARD_VAT_PERCENT
    return True, percent / Decimal("100")


async def vat_position_on(db: AsyncSession, on: date) -> tuple[bool, Decimal, Decimal]:
    """(charge_vat, rate_fraction, rate_percent) from the company profile."""
    result = await db.execute(select(CompanyProfile).limit(1))
    profile = result.scalar_one_or_none()
    if profile is None:
        return False, Decimal("0"), Decimal("0")
    charge, fraction = vat_applies(
        profile.vat_status,
        profile.vat_effective_from,
        on,
        profile.vat_rate_percent,
    )
    percent = (fraction * Decimal("100")) if charge else Decimal("0")
    return charge, fraction, percent
