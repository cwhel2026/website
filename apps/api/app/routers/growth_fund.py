"""SurfaceCoat Growth Fund API."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_accountant_or_admin
from app.database import get_db
from app.models.user import User
from app.services.marketing.growth_fund import (
    fund_summary,
    get_or_create_settings,
    ledger_entries,
    process_revenue_allocations,
    record_initial_launch_contribution,
    record_manual_contribution,
)

router = APIRouter(prefix="/finance/growth-fund", tags=["growth-fund"])


@router.get("/summary")
async def summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
) -> dict:
    return await fund_summary(db)


@router.get("/ledger")
async def ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_accountant_or_admin)],
    limit: int = 100,
) -> dict:
    entries = await ledger_entries(db, limit=limit)
    summary_data = await fund_summary(db)
    return {"summary": summary_data, "entries": entries}


class SettingsPatch(BaseModel):
    allocation_pct: Decimal | None = None
    enabled: bool | None = None
    initial_launch_contribution_gbp: Decimal | None = None


@router.get("/settings")
async def settings_get(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    s = await get_or_create_settings(db)
    return {
        "allocation_pct": float(s.allocation_pct),
        "enabled": s.enabled,
        "initial_launch_contribution_gbp": float(s.initial_launch_contribution_gbp),
        "initial_launch_recorded": s.initial_launch_recorded,
        "mettle_pot_status": s.mettle_pot_status,
    }


@router.patch("/settings")
async def settings_patch(
    body: SettingsPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    s = await get_or_create_settings(db)
    if body.allocation_pct is not None:
        s.allocation_pct = body.allocation_pct
    if body.enabled is not None:
        s.enabled = body.enabled
    if body.initial_launch_contribution_gbp is not None:
        s.initial_launch_contribution_gbp = body.initial_launch_contribution_gbp
    await db.commit()
    return {"ok": True}


class ManualContribution(BaseModel):
    amount_gbp: Decimal
    description: str
    idempotency_key: str


@router.post("/manual-contribution")
async def manual_contribution(
    body: ManualContribution,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    await record_manual_contribution(
        db,
        amount_gbp=body.amount_gbp,
        description=body.description,
        dedupe_key=f"manual:{body.idempotency_key}",
    )
    await db.commit()
    return {"ok": True}


@router.post("/record-initial-launch")
async def record_initial(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await record_initial_launch_contribution(db)
    await db.commit()
    return result


@router.post("/process-allocations")
async def process_allocations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await process_revenue_allocations(db, notify=True)
    await db.commit()
    return result