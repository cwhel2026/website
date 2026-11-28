from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_admin_writer
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.workspace import WorkspaceConnection
from app.services import workspace_connection
from app.services.finance.token_vault import encryption_configured

router = APIRouter(prefix="/integrations/google", tags=["workspace"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/status")
async def status(db: DB, _: Annotated[User, Depends(get_current_admin)]) -> dict:
    settings = get_settings()
    configured = bool(settings.google_client_id and settings.google_client_secret
                      and settings.google_redirect_uri and encryption_configured())
    row = await db.get(WorkspaceConnection, 1)
    return {"configured": configured,
            "authorized": bool(configured and row and row.refresh_token
                               and row.email == settings.google_workspace_email),
            "email": settings.google_workspace_email,
            "live_connection_verified": False}


@router.post("/connect")
async def connect(db: DB, _: Annotated[User, Depends(get_current_admin_writer)]) -> dict:
    try:
        return {"authorize_url": await workspace_connection.begin(db)}
    except ValueError:
        raise HTTPException(409, "Workspace configuration incomplete") from None


@router.get("/callback")
async def callback(db: DB, code: Annotated[str, Query(min_length=1, max_length=4096)],
                   state: Annotated[str, Query(min_length=1, max_length=256)]) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await workspace_connection.complete(db, client, code, state)
    except (ValueError, httpx.HTTPError, KeyError):
        raise HTTPException(400, "Workspace authorization failed; restart connection") from None
    return {"authorized": True}
