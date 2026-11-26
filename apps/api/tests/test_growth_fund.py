from decimal import Decimal

import pytest

from app.services.marketing.growth_fund_eligibility import eligible_revenue_gbp, is_excluded_description


def test_excludes_internal_transfer():
    assert is_excluded_description("Internal transfer to savings")


@pytest.mark.asyncio
async def test_vat_exclusive_allocation_base():
    from types import SimpleNamespace
    from uuid import uuid4

    from app.models.finance import InvoiceStatus

    txn = SimpleNamespace(
        amount_gbp=Decimal("120"),
        is_duplicate=False,
        is_reconciled=True,
        matched_invoice_id=uuid4(),
        description="Customer payment INV-001",
    )
    inv = SimpleNamespace(
        status=InvoiceStatus.PAID,
        subtotal_ex_vat_gbp=Decimal("100"),
        total_inc_vat_gbp=Decimal("120"),
    )
    base = await eligible_revenue_gbp(txn, inv)
    assert base == Decimal("100.00")


@pytest.mark.asyncio
async def test_zero_for_excluded():
    from types import SimpleNamespace

    txn = SimpleNamespace(
        amount_gbp=Decimal("500"),
        is_duplicate=False,
        is_reconciled=True,
        matched_invoice_id=None,
        description="Director capital contribution",
    )
    base = await eligible_revenue_gbp(txn, None)
    assert base == Decimal("0")