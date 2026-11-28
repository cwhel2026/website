from decimal import Decimal as D

import pytest

from app.services.finance.booking_amounts import booking_amounts, outstanding_balance


def test_default_deposit():
    assert booking_amounts(D("1000"), D("200")) == (D("100"), D("20"), D("120"))
    assert outstanding_balance(D("1200"), D("120")) == D("1080")


def test_custom_deposit_and_rounding():
    net, vat, gross = booking_amounts(D("83.33"), D("16.67"), D("25"))
    assert gross == D("25.00")
    assert net + vat == gross


@pytest.mark.parametrize("percent", ["0", "-1", "101", "NaN"])
def test_invalid_deposit(percent):
    with pytest.raises(ValueError):
        booking_amounts(D("100"), D("0"), D(percent))


def test_overpayment_requires_review():
    with pytest.raises(ValueError):
        outstanding_balance(D("100"), D("101"))
