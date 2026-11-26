"""SurfaceCoat Growth Fund — virtual reserve; no simulated bank transfers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BankTransaction, Invoice
from app.models.marketing import CampaignStatus, RegionalCampaign
from app.models.marketing_growth_fund import (
    GrowthFundEntryType,
    MarketingGrowthFundLedger,
    MarketingGrowthFundSettings,
)
from app.services.marketing.growth_fund_eligibility import eligible_revenue_gbp


METTLE_POT_RESEARCH = {
    "automated_pot_transfers": False,
    "reason": "Mettle has no public Open Banking pot API in this platform — bank feed is via FreeAgent.",
    "recommendation": "Maintain virtual reserve here; manually move cash in Mettle if you use pots.",
    "simulated_transfers": False,
}


async def get_or_create_settings(db: AsyncSession) -> MarketingGrowthFundSettings:
    row = (await db.execute(select(MarketingGrowthFundSettings).limit(1))).scalar_one_or_none()
    if row is None:
        row = MarketingGrowthFundSettings(
            allocation_pct=Decimal("5"),
            initial_launch_contribution_gbp=Decimal("600"),
            mettle_pot_status="virtual_reserve",
            notes=METTLE_POT_RESEARCH["reason"],
        )
        db.add(row)
        await db.flush()
    return row


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def ledger_balance(db: AsyncSession) -> Decimal:
    total = await db.scalar(select(func.coalesce(func.sum(MarketingGrowthFundLedger.amount_gbp), 0)))
    return _q(Decimal(str(total or 0)))


async def allocated_for_invoice(db: AsyncSession, invoice_id) -> Decimal:
    total = await db.scalar(
        select(func.coalesce(func.sum(MarketingGrowthFundLedger.eligible_revenue_gbp), 0)).where(
            MarketingGrowthFundLedger.invoice_id == invoice_id,
            MarketingGrowthFundLedger.entry_type == GrowthFundEntryType.REVENUE_ALLOCATION,
        )
    )
    return _q(Decimal(str(total or 0)))


async def committed_ad_budget(db: AsyncSession) -> Decimal:
    """Campaign budgets not yet reflected in spent_gbp — conservative estimate."""
    rows = (
        await db.execute(
            select(RegionalCampaign).where(
                RegionalCampaign.simulation_only.is_(False),
                RegionalCampaign.status.in_(
                    (CampaignStatus.LIVE, CampaignStatus.APPROVED, CampaignStatus.PAUSED, CampaignStatus.DRAFT)
                ),
            )
        )
    ).scalars().all()
    committed = Decimal("0")
    for c in rows:
        committed += Decimal(str(c.daily_budget_gbp or 0)) * Decimal("7")
    return _q(committed)


async def fund_summary(db: AsyncSession) -> dict:
    settings = await get_or_create_settings(db)
    balance = await ledger_balance(db)
    committed = await committed_ad_budget(db)
    available = _q(balance - committed)
    since_week = datetime.now(UTC) - timedelta(days=7)
    since_month = datetime.now(UTC) - timedelta(days=30)
    week_alloc = await db.scalar(
        select(func.coalesce(func.sum(MarketingGrowthFundLedger.amount_gbp), 0)).where(
            MarketingGrowthFundLedger.entry_type == GrowthFundEntryType.REVENUE_ALLOCATION,
            MarketingGrowthFundLedger.created_at >= since_week,
        )
    )
    month_alloc = await db.scalar(
        select(func.coalesce(func.sum(MarketingGrowthFundLedger.amount_gbp), 0)).where(
            MarketingGrowthFundLedger.entry_type == GrowthFundEntryType.REVENUE_ALLOCATION,
            MarketingGrowthFundLedger.created_at >= since_month,
        )
    )
    return {
        "virtual_reserve_balance_gbp": float(balance),
        "committed_ad_budget_gbp": float(committed),
        "available_uncommitted_gbp": float(max(Decimal("0"), available)),
        "allocation_pct": float(settings.allocation_pct),
        "enabled": settings.enabled,
        "mettle_pots": METTLE_POT_RESEARCH,
        "weekly_allocations_gbp": float(week_alloc or 0),
        "monthly_allocations_gbp": float(month_alloc or 0),
        "is_virtual_not_bank_balance": True,
        "weekly_ad_limit_unchanged_note": "£150/week cap remains until owner increases approved limits.",
    }


async def record_manual_contribution(
    db: AsyncSession,
    *,
    amount_gbp: Decimal,
    description: str,
    dedupe_key: str,
) -> MarketingGrowthFundLedger:
    entry = MarketingGrowthFundLedger(
        entry_type=GrowthFundEntryType.MANUAL_CONTRIBUTION,
        amount_gbp=_q(amount_gbp),
        dedupe_key=dedupe_key,
        description=description,
    )
    db.add(entry)
    await db.flush()
    return entry


async def record_initial_launch_contribution(db: AsyncSession) -> dict:
    settings = await get_or_create_settings(db)
    if settings.initial_launch_recorded:
        return {"ok": False, "message": "Initial launch contribution already recorded"}
    amount = _q(settings.initial_launch_contribution_gbp or Decimal("600"))
    if amount <= 0:
        return {"ok": False, "message": "Set initial_launch_contribution_gbp first"}
    await record_manual_contribution(
        db,
        amount_gbp=amount,
        description="Initial launch marketing fund (£150 × 4 weeks) — record when genuinely funded",
        dedupe_key="manual:initial-launch-600",
    )
    settings.initial_launch_recorded = True
    await db.flush()
    return {"ok": True, "amount_gbp": float(amount)}


async def process_revenue_allocations(db: AsyncSession, *, notify: bool = True) -> dict:
    settings = await get_or_create_settings(db)
    if not settings.enabled:
        return {"processed": 0, "message": "Growth fund disabled"}

    pct = settings.allocation_pct / Decimal("100")
    existing_keys = {
        x
        for x in (
            await db.execute(select(MarketingGrowthFundLedger.dedupe_key))
        ).scalars().all()
    }

    txns = (
        await db.execute(
            select(BankTransaction).where(
                BankTransaction.amount_gbp > 0,
                BankTransaction.is_duplicate.is_(False),
            )
        )
    ).scalars().all()

    processed = 0
    notifications: list[dict] = []

    for txn in txns:
        dedupe = f"alloc:bank:{txn.external_id or txn.id}"
        if dedupe in existing_keys:
            continue

        invoice = None
        if txn.matched_invoice_id:
            invoice = (
                await db.execute(select(Invoice).where(Invoice.id == txn.matched_invoice_id))
            ).scalar_one_or_none()

        eligible = await eligible_revenue_gbp(txn, invoice)
        if eligible <= 0:
            continue

        if invoice:
            already = await allocated_for_invoice(db, invoice.id)
            remaining_ex_vat = _q(invoice.subtotal_ex_vat_gbp - already)
            if remaining_ex_vat <= 0:
                continue
            eligible = min(eligible, remaining_ex_vat)

        allocation = _q(eligible * pct)
        if allocation <= 0:
            continue

        db.add(
            MarketingGrowthFundLedger(
                entry_type=GrowthFundEntryType.REVENUE_ALLOCATION,
                amount_gbp=allocation,
                eligible_revenue_gbp=eligible,
                allocation_pct=settings.allocation_pct,
                bank_transaction_id=txn.id,
                invoice_id=invoice.id if invoice else None,
                dedupe_key=dedupe,
                description=f"5% of eligible revenue from «{txn.description[:80]}»",
                metadata_json={"source": "freeagent_bank", "reconciled": txn.is_reconciled},
            )
        )
        existing_keys.add(dedupe)
        processed += 1
        if notify and allocation > 0:
            balance = await ledger_balance(db)
            notifications.append(
                {
                    "payment_gbp": float(txn.amount_gbp),
                    "allocation_gbp": float(allocation),
                    "available_gbp": float(balance + allocation),
                }
            )

    if notify and notifications:
        from app.services.notifications.outbox import enqueue_notification

        n = notifications[-1]
        body = (
            f"Customer payment received: £{n['payment_gbp']:.2f}\n"
            f"Marketing allocation: £{n['allocation_gbp']:.2f}\n"
            f"Available marketing fund: £{n['available_gbp']:.2f}\n"
            "Current weekly advertising limit: £150 (unchanged until you approve an increase)"
        )
        await enqueue_notification(
            db,
            channel="telegram",
            title="SurfaceCoat Growth Fund",
            body=body,
            category="marketing_growth_fund",
            dedupe_key=f"growth-fund:{datetime.now(UTC).date().isoformat()}:{processed}",
        )

    refund_count = await _process_refund_reversals(db, existing_keys, settings.allocation_pct)
    return {
        "processed": processed,
        "refunds": refund_count,
        "allocation_pct": float(settings.allocation_pct),
    }


async def _process_refund_reversals(db: AsyncSession, existing_keys: set[str], allocation_pct: Decimal) -> int:
    pct = allocation_pct / Decimal("100")
    txns = (
        await db.execute(
            select(BankTransaction).where(
                BankTransaction.amount_gbp < 0,
                BankTransaction.is_reconciled.is_(True),
                BankTransaction.is_duplicate.is_(False),
            )
        )
    ).scalars().all()
    count = 0
    for txn in txns:
        dedupe = f"refund:bank:{txn.external_id or txn.id}"
        if dedupe in existing_keys:
            continue
        eligible = abs(txn.amount_gbp).quantize(Decimal("0.01"))
        reversal = _q(-(eligible * pct))
        db.add(
            MarketingGrowthFundLedger(
                entry_type=GrowthFundEntryType.REFUND_ADJUSTMENT,
                amount_gbp=reversal,
                eligible_revenue_gbp=eligible,
                allocation_pct=allocation_pct,
                bank_transaction_id=txn.id,
                dedupe_key=dedupe,
                description=f"Reversal of marketing allocation on refund «{txn.description[:60]}»",
            )
        )
        count += 1
    return count


async def ledger_entries(db: AsyncSession, limit: int = 100) -> list[dict]:
    rows = (
        await db.execute(
            select(MarketingGrowthFundLedger)
            .order_by(MarketingGrowthFundLedger.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": str(r.id),
            "type": r.entry_type.value,
            "amount_gbp": float(r.amount_gbp),
            "eligible_revenue_gbp": float(r.eligible_revenue_gbp) if r.eligible_revenue_gbp else None,
            "description": r.description,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]