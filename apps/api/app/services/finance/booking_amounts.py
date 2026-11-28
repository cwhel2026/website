from decimal import Decimal, ROUND_HALF_UP

PENNY = Decimal("0.01")


def booking_amounts(net: Decimal, vat: Decimal, percent: Decimal = Decimal("10")) -> tuple[Decimal, Decimal, Decimal]:
    """Return deposit net, VAT and gross; never use binary floating point."""
    if not all(x.is_finite() for x in (net, vat, percent)):
        raise ValueError("Amounts must be finite")
    if net < 0 or vat < 0 or net + vat <= 0 or not 0 < percent <= 100:
        raise ValueError("Invalid booking amount or percentage")
    if net != net.quantize(PENNY) or vat != vat.quantize(PENNY):
        raise ValueError("Amounts must be in whole pennies")
    gross = ((net + vat) * percent / 100).quantize(PENNY, rounding=ROUND_HALF_UP)
    deposit_vat = (vat * percent / 100).quantize(PENNY, rounding=ROUND_HALF_UP)
    if gross <= 0:
        raise ValueError("Deposit must be at least one penny")
    return gross - deposit_vat, deposit_vat, gross


def outstanding_balance(total: Decimal, confirmed_paid: Decimal) -> Decimal:
    if not all(x.is_finite() for x in (total, confirmed_paid)):
        raise ValueError("Amounts must be finite")
    if total < 0 or not 0 <= confirmed_paid <= total:
        raise ValueError("Payment balance requires review")
    if total != total.quantize(PENNY) or confirmed_paid != confirmed_paid.quantize(PENNY):
        raise ValueError("Amounts must be in whole pennies")
    return total - confirmed_paid
