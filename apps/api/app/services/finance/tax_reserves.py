import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import TaxReserveSnapshot
from app.models.company import CompanyProfile, PayrollStatus, VatStatus
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.finance.freeagent_reports import _extract_net_profit_before_tax, get_cached_report
from app.services.tax_engine.marginal_relief import corporation_tax_with_marginal_relief
from app.services.tax_engine.rules_uk_ltd import rules_for_date
from app.services.tax_engine.vat_monitor import rolling_vat_taxable_turnover


def _liability_bucket(*, known: bool, amount: Decimal | None, note: str) -> dict:
    if not known or amount is None:
        return {"status": "unknown", "amount_gbp": None, "note": note}
    return {"status": "estimated", "amount_gbp": float(amount), "note": note}


async def compute_tax_reserves(db: AsyncSession) -> dict:
    rules = rules_for_date()
    fa = await freeagent_status(db)
    now = datetime.now(UTC)
    sync_age_hours: float | None = None
    if fa.last_sync_at:
        sync_age_hours = (now - fa.last_sync_at).total_seconds() / 3600.0
    data_stale = sync_age_hours is None or sync_age_hours > 168
    data_complete = fa.can_sync and not data_stale

    pl = await get_cached_report(db, "pl_summary_ytd")
    net_profit = _extract_net_profit_before_tax(pl or {}) if pl else None

    profile = await db.execute(select(CompanyProfile).limit(1))
    prof = profile.scalar_one_or_none()

    ct_known = False
    ct_amount: Decimal | None = None
    if net_profit is not None and data_complete:
        ct = corporation_tax_with_marginal_relief(max(Decimal("0"), net_profit))
        ct_amount = Decimal(str(ct["corporation_tax_gbp"]))
        ct_known = True
    ct_bucket = _liability_bucket(
        known=ct_known,
        amount=ct_amount,
        note="From cached FreeAgent P&L retained movement when sync <7d." if ct_known else "Connect FreeAgent and sync reports.",
    )

    vat = await rolling_vat_taxable_turnover(db)
    vat_known = prof is not None and prof.vat_status in (VatStatus.REGISTERED, VatStatus.APPLIED)
    vat_amount: Decimal | None = None
    if vat_known:
        # Not a filing estimate — rough liability reserve only when registered
        net_taxable = Decimal(str(vat["taxable_turnover_gbp"])) * Decimal("0.2") * Decimal("0.17")
        vat_amount = net_taxable.quantize(Decimal("0.01"))
    elif vat.get("registration_may_be_required"):
        vat_amount = Decimal("0")
    vat_bucket = _liability_bucket(
        known=vat_known or vat.get("data_complete") is False,
        amount=vat_amount,
        note="VAT reserve only when registration status confirmed.",
    )

    paye_known = prof is not None and prof.paye_status == PayrollStatus.REGISTERED
    paye_bucket = _liability_bucket(
        known=paye_known,
        amount=Decimal("0") if paye_known else None,
        note="PAYE/NI accrual requires FreeAgent payroll read — set PAYE status on company profile.",
    )

    known_amounts = [
        b["amount_gbp"] for b in (ct_bucket, vat_bucket, paye_bucket) if b["status"] != "unknown" and b["amount_gbp"] is not None
    ]
    recommended = sum((Decimal(str(a)) for a in known_amounts), Decimal("0"))
    has_unknown = any(b["status"] == "unknown" for b in (ct_bucket, vat_bucket, paye_bucket))

    snapshot = TaxReserveSnapshot(
        rule_version=rules.version,
        corporation_tax_gbp=str(ct_bucket["amount_gbp"] if ct_bucket["amount_gbp"] is not None else "unknown"),
        vat_provision_gbp=str(vat_bucket["amount_gbp"] if vat_bucket["amount_gbp"] is not None else "unknown"),
        paye_provision_gbp=str(paye_bucket["amount_gbp"] if paye_bucket["amount_gbp"] is not None else "unknown"),
        recommended_total_gbp=str(float(recommended)) if not has_unknown else "unknown",
        assumptions_json=json.dumps(
            {
                "sync_age_hours": sync_age_hours,
                "data_stale": data_stale,
                "has_unknown_liabilities": has_unknown,
            }
        ),
        data_freshness_note=(
            f"FreeAgent sync {sync_age_hours:.0f}h ago" if sync_age_hours is not None else "FreeAgent never synced"
        ),
        is_provisional=data_stale or has_unknown or not fa.can_sync,
    )
    db.add(snapshot)
    await db.flush()

    return {
        "recommended_reserve_gbp": float(recommended) if not has_unknown else None,
        "corporation_tax": ct_bucket,
        "vat": vat_bucket,
        "paye": paye_bucket,
        "has_unknown_liabilities": has_unknown,
        "is_provisional": snapshot.is_provisional,
        "data_stale": data_stale,
        "sync_age_hours": sync_age_hours,
        "data_complete": data_complete,
        "vat_monitor": vat,
        "rule_version": rules.version,
        "tax_year_label": rules.tax_year_label,
        "sources": list(rules.sources),
        "verified_on": rules.verified_on,
        "plain_english": (
            "Some statutory liabilities are unknown — do not treat missing amounts as zero."
            if has_unknown
            else "Known liability buckets summed for cash planning — not a filing."
        ),
        "snapshot_id": str(snapshot.id),
    }