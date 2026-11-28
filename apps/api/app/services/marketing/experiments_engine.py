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
    return {"ok": True, "insufficient_data": True, "message": "Variant-level comparable outcomes are not recorded. No winner can be established."}


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