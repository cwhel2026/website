"""Marketing experiments with minimum sample guards."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_experiment import ExperimentStatus, MarketingExperiment


async def evaluate_experiment(db: AsyncSession, experiment_id) -> dict:
    exp = await db.get(MarketingExperiment, experiment_id)
    if exp is None:
        return {"ok": False, "message": "Not found"}
    sample = exp.enquiries + exp.quotations + exp.bookings
    if sample < exp.min_sample_size:
        return {
            "ok": True,
            "insufficient_data": True,
            "message": f"Need {exp.min_sample_size} samples; have {sample}",
        }
    if exp.quotations == 0:
        return {"ok": True, "insufficient_data": True, "message": "No quotation outcomes yet"}
    rate_a = float(exp.revenue_gbp) if exp.variant_a else 0
    rate_b = float(exp.enquiries) / max(exp.quotations, 1)
    winner = "A" if rate_a >= rate_b else "B"
    exp.winner_variant = winner
    exp.conclusion = f"Provisional winner {winner} on {exp.metric_name} (sample {sample})"
    exp.status = ExperimentStatus.COMPLETED
    await db.flush()
    return {"ok": True, "winner": winner, "conclusion": exp.conclusion}


async def list_experiments(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(select(MarketingExperiment).order_by(MarketingExperiment.created_at.desc()))).scalars().all()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "status": e.status.value,
            "hypothesis": e.hypothesis,
            "min_sample_size": e.min_sample_size,
            "conclusion": e.conclusion,
        }
        for e in rows
    ]