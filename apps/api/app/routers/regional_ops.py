from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.jobs import Appointment, Job
from app.models.territory import Territory
from app.models.user import User

router = APIRouter(prefix="/regional", tags=["regional"])


class TerritoryLoadOut(BaseModel):
    territory_code: str
    territory_name: str
    appointment_count: int
    job_references: list[str]


@router.get("/workload", response_model=list[TerritoryLoadOut])
async def regional_workload(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
) -> list[TerritoryLoadOut]:
    result = await db.execute(
        select(Appointment, Job, Territory)
        .join(Job)
        .outerjoin(Territory, Job.territory_id == Territory.id)
        .where(Appointment.scheduled_start >= from_dt, Appointment.scheduled_start <= to_dt)
    )
    buckets: dict[str, TerritoryLoadOut] = {}
    refs: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)
    names: dict[str, str] = {}
    for appt, job, territory in result.all():
        code = territory.code if territory else "?"
        names[code] = territory.name if territory else "Unassigned"
        counts[code] += 1
        refs[code].add(job.reference)
    for code, count in counts.items():
        buckets[code] = TerritoryLoadOut(
            territory_code=code,
            territory_name=names[code],
            appointment_count=count,
            job_references=sorted(refs[code]),
        )
    return sorted(buckets.values(), key=lambda x: x.territory_code)