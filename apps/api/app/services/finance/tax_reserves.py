import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import TaxReserveSnapshot
from app.models.finance import Expense, Invoice, InvoiceStatus, Payment
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES
from app.services.tax_engine.vat_monitor import rolling_vat_taxable_turnover


async def compute_tax_reserves(db: AsyncSession) -> dict:
    fa = await freeagent_status(db)
    stale = fa.last_sync_at is None if fa.can_sync else True
    freshness = (
        f"FreeAgent last sync: {fa.last_sync_at.isoformat() if fa.last_sync_at else 'never'}"
        if fa.can_sync
        else "FreeAgent not connected — reserves use local invoices/expenses only."
    )

    inv = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.PAID, InvoiceStatus.OVERDUE])
        )
    )
    revenue = sum((i.subtotal_ex_vat_gbp for i in inv.scalars().all()), Decimal("0"))
    payments = await db.execute(select(Payment))
    collected = sum((p.amount_gbp for p in payments.scalars().all()), Decimal("0"))
    exp = await db.execute(select(Expense))
    expenses = sum((e.amount_gbp for e in exp.scalars().all()), Decimal("0"))

    profit_estimate = max(Decimal("0"), revenue - expenses)
    ct = corporation_tax_with_marginal_relief(profit_estimate)
    vat = await rolling_vat_taxable_turnover(db)
    vat_provision = Decimal("0")
    if vat.get("registration_may_be_required"):
        vat_provision = Decimal(str(vat["taxable_turnover_gbp"])) * Decimal("0.17")

    paye_provision = Decimal("0")
    recommended = Decimal(str(ct["corporation_tax_gbp"])) + vat_provision + paye_provision

    provisional = stale or not fa.can_sync
    snapshot = TaxReserveSnapshot(
        rule_version=ACTIVE_RULES.version,
        corporation_tax_gbp=str(ct["corporation_tax_gbp"]),
        vat_provision_gbp=str(float(vat_provision)),
        paye_provision_gbp=str(float(paye_provision)),
        recommended_total_gbp=str(float(recommended)),
        assumptions_json=json.dumps(
            {
                "profit_estimate_gbp": float(profit_estimate),
                "revenue_invoices_gbp": float(revenue),
                "collected_payments_gbp": float(collected),
                "expenses_gbp": float(expenses),
            }
        ),
        data_freshness_note=freshness,
        is_provisional=provisional,
    )
    db.add(snapshot)
    await db.flush()

    return {
        "recommended_reserve_gbp": float(recommended),
        "corporation_tax_gbp": ct["corporation_tax_gbp"],
        "vat_provision_gbp": float(vat_provision),
        "paye_provision_gbp": float(paye_provision),
        "profit_estimate_gbp": float(profit_estimate),
        "vat_monitor": vat,
        "is_provisional": provisional,
        "data_freshness": freshness,
        "rule_version": ACTIVE_RULES.version,
        "sources": ACTIVE_RULES.sources,
        "plain_english": (
            "These are planning figures — money has not been moved. Keep cash aside based on accountant advice."
            if not provisional
            else "Data is incomplete or stale. Treat all reserve figures as provisional until books are up to date."
        ),
        "snapshot_id": str(snapshot.id),
    }