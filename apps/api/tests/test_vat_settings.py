from datetime import date
from decimal import Decimal

from app.models.company import VatStatus
from app.services.vat_settings import vat_applies


def test_unregistered_and_future_dates_do_not_charge_vat():
    on = date(2026, 11, 27)
    assert vat_applies(VatStatus.NOT_REGISTERED, None, on, Decimal("20")) == (False, Decimal("0"))
    assert vat_applies(VatStatus.APPLIED, None, on, Decimal("20")) == (False, Decimal("0"))
    assert vat_applies(VatStatus.UNKNOWN, date(2026, 1, 1), on, Decimal("20")) == (False, Decimal("0"))
    assert vat_applies(VatStatus.REGISTERED, date(2027, 4, 1), on, Decimal("20")) == (False, Decimal("0"))


def test_registered_on_or_after_the_effective_date_charges_the_configured_rate():
    on = date(2027, 4, 1)
    charge, rate = vat_applies(VatStatus.REGISTERED, date(2027, 4, 1), on, Decimal("20"))
    assert charge is True
    assert rate == Decimal("0.2")
    later, later_rate = vat_applies(VatStatus.REGISTERED, None, on, Decimal("5"))
    assert later is True
    assert later_rate == Decimal("0.05")
