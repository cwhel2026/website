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


@pytest.mark.asyncio
async def test_invoice_pagination(monkeypatch):
    from app.services.finance import freeagent_client as client
    from unittest.mock import AsyncMock
    mock = AsyncMock(side_effect=[{"invoices": [{"url": str(i)} for i in range(50)]}, {"invoices": [{"url": "50"}]}])
    monkeypatch.setattr(client, "api_get", mock)
    assert len(await client.fetch_invoices(SimpleNamespace(), "token")) == 51
    assert mock.await_count == 2


@pytest.mark.asyncio
async def test_pagination_limit_is_not_success(monkeypatch):
    from app.services.finance import freeagent_client as client
    from unittest.mock import AsyncMock
    monkeypatch.setattr(client, "api_get", AsyncMock(return_value={"invoices": [{}] * 50}))
    with pytest.raises(ValueError, match="incomplete"):
        await client.fetch_paginated_list(SimpleNamespace(), "token", "/v2/invoices", "invoices", max_pages=1)


@pytest.mark.asyncio
async def test_foreign_bank_account_origin_rejected(monkeypatch):
    from app.services.finance import freeagent_client as client
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    monkeypatch.setattr(client, "api_get", mock)
    with pytest.raises(ValueError):
        await client.fetch_bank_transactions(SimpleNamespace(freeagent_api_base="https://api.freeagent.com"), "token", "https://other.example/v2/bank_accounts/1")
    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_invoice_linked_revenue_excludes_vat():
    txn = SimpleNamespace(is_duplicate=False, amount_gbp=Decimal("120"), is_reconciled=True, matched_invoice_id="invoice", description="Customer payment")
    inv = SimpleNamespace(status=InvoiceStatus.PAID, total_inc_vat_gbp=Decimal("120"), subtotal_ex_vat_gbp=Decimal("100"))
    assert await eligible_revenue_gbp(txn, inv) == Decimal("100.00")
