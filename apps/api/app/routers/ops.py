"""Operational evidence for the owner: schema state and background job health."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.worker_health import worker_health

router = APIRouter(prefix="/ops", tags=["ops"])


def _broker_ping() -> bool:
    import redis

    from app.worker.guard import redis_client

    try:
        return bool(redis_client().ping())
    except redis.RedisError:
        return False


def _schema_report() -> dict:
    from app.schema.audit import schema_report

    engine = create_engine(get_settings().sync_database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            return schema_report(conn)
    finally:
        engine.dispose()


@router.get("/workers")
async def workers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    try:
        ping = await asyncio.wait_for(asyncio.to_thread(_broker_ping), timeout=5)
    except TimeoutError:
        ping = False
    return await worker_health(db, broker_ping=ping)


@router.get("/schema")
async def schema(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return await asyncio.to_thread(_schema_report)
