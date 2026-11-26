"""Determine whether a reconciled bank inflow counts as customer revenue for Growth Fund."""

from __future__ import annotations

import re
from decimal import Decimal

from app.models.finance import BankTransaction, Invoice, InvoiceStatus

_EXCLUDE = re.compile(
    r"\b(transfer|internal|loan|director|capital|dividend|hmrc\s*vat|vat\s*repayment|"
    r"interest\s*received|savings|mettle\s*pot|refund\s*from\s*supplier)\b",
    re.I,
)


def is_excluded_description(description: str) -> bool:
    return bool(_EXCLUDE.search(description or ""))


async def eligible_revenue_gbp(
    txn: BankTransaction,
    invoice: Invoice | None,
) -> Decimal:
    """VAT-exclusive eligible portion of this inflow."""
    if txn.is_duplicate or txn.amount_gbp <= 0:
        return Decimal("0")
    if not txn.is_reconciled and not txn.matched_invoice_id:
        return Decimal("0")
    if is_excluded_description(txn.description):
        return Decimal("0")

    amount = txn.amount_gbp.quantize(Decimal("0.01"))

    if invoice and invoice.status not in (InvoiceStatus.VOID, InvoiceStatus.DRAFT):
        if invoice.total_inc_vat_gbp <= 0:
            return Decimal("0")
        ex_vat_ratio = (invoice.subtotal_ex_vat_gbp / invoice.total_inc_vat_gbp).quantize(Decimal("0.0001"))
        ex_vat_portion = (amount * ex_vat_ratio).quantize(Decimal("0.01"))
        return min(ex_vat_portion, invoice.subtotal_ex_vat_gbp)

    if txn.amount_gbp > 0 and txn.is_reconciled:
        return amount

    return Decimal("0")