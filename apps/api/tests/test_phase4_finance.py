from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.finance import InvoiceStatus
from app.services.finance.freeagent_adapter import apply_remote_invoice_balance
from app.services.marketing.growth_fund_eligibility import eligible_revenue_gbp


def test_remote_partial_payment():
    invoice = SimpleNamespace()
    assert apply_remote_invoice_balance(invoice, {"currency": "GBP", "total_value": "120", "net_value": "100", "due_value": "60", "status": "Sent"})
    assert invoice.amount_paid_gbp == Decimal("60")
    assert invoice.vat_gbp == Decimal("20")
    assert invoice.status == InvoiceStatus.PART_PAID


@pytest.mark.parametrize("due", ["NaN", "-1", "121"])
def test_invalid_remote_balance_does_not_mutate(due):
    invoice = SimpleNamespace(amount_paid_gbp=Decimal("5"))
    assert not apply_remote_invoice_balance(invoice, {"total_value": "120", "net_value": "100", "due_value": due, "status": "Sent"})
    assert invoice.amount_paid_gbp == Decimal("5")


@pytest.mark.asyncio
async def test_unmatched_bank_inflow_not_revenue():
    txn = SimpleNamespace(is_duplicate=False, amount_gbp=Decimal("100"), is_reconciled=True, matched_invoice_id=None, description="Unknown receipt")
    assert await eligible_revenue_gbp(txn, None) == 0
