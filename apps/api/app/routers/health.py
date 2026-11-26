from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import get_db

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health() -> dict[str, str | None]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": "0.8.0",
        "git_commit": settings.git_commit,
        "build_time": settings.build_time,
    }


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": "database"},
        )
    try:
        current = (await db.execute(text("SELECT version_num FROM alembic_version"))).scalar()
    except Exception:
        await db.rollback()
        current = None
    head = _alembic_head()
    if current != head:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": "schema", "schema_revision": current, "schema_head": head},
        )
    return {"status": "ready", "database": "ok", "schema_revision": current}


def _alembic_head() -> str | None:
    global _HEAD
    if _HEAD is None:
        from app.schema.audit import alembic_head

        _HEAD = alembic_head()
    return _HEAD


_HEAD: str | None = None