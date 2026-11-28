import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.workspace import WorkspaceConnection
from app.services import google_workspace as google
from app.services.finance.token_vault import (
    decrypt_token, encrypt_token, encryption_configured,
)


def _settings():
    settings = get_settings()
    if not all((settings.google_client_id, settings.google_client_secret,
                settings.google_redirect_uri, encryption_configured())):
        raise ValueError("Workspace OAuth or token encryption not configured")
    return settings


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def begin(db: AsyncSession) -> str:
    settings = _settings()
    await db.execute(insert(WorkspaceConnection).values(id=1).on_conflict_do_nothing())
    row = await db.get(WorkspaceConnection, 1, with_for_update=True)
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    row.oauth_state_hash = _digest(state)
    row.oauth_verifier = encrypt_token(verifier)
    row.oauth_expires_at = datetime.now(UTC) + timedelta(minutes=10)
    await db.commit()
    return google.authorization_url(settings.google_client_id, settings.google_redirect_uri,
                                    state, challenge)


async def complete(db: AsyncSession, client: httpx.AsyncClient, code: str, state: str) -> None:
    settings = _settings()
    row = await db.get(WorkspaceConnection, 1, with_for_update=True)
    if (not row or not row.oauth_state_hash or not row.oauth_expires_at
            or row.oauth_expires_at <= datetime.now(UTC)
            or not hmac.compare_digest(row.oauth_state_hash, _digest(state))):
        raise ValueError("Invalid or expired OAuth state")
    verifier = decrypt_token(row.oauth_verifier)
    row.oauth_state_hash = row.oauth_verifier = row.oauth_expires_at = None
    await db.commit()
    if not verifier:
        raise ValueError("Missing OAuth verifier")
    tokens = await google.exchange_code(client, client_id=settings.google_client_id,
        client_secret=settings.google_client_secret, redirect_uri=settings.google_redirect_uri,
        code=code, verifier=verifier)
    identity = await google.WorkspaceClient(client, tokens["access_token"]).identity()
    if (identity.get("verified_email") is not True
            or identity.get("email", "").lower() != settings.google_workspace_email.lower()):
        raise ValueError("Incorrect Workspace mailbox")
    if not tokens.get("refresh_token"):
        raise ValueError("Google did not grant offline access")
    row = await db.get(WorkspaceConnection, 1, with_for_update=True)
    row.email = identity["email"]
    row.access_token = encrypt_token(tokens["access_token"])
    row.refresh_token = encrypt_token(tokens["refresh_token"])
    row.expires_at = datetime.now(UTC) + timedelta(seconds=int(tokens["expires_in"]))
    await db.commit()


async def access_token(db: AsyncSession, client: httpx.AsyncClient) -> str:
    settings = _settings()
    row = await db.get(WorkspaceConnection, 1, with_for_update=True)
    if not row or not row.refresh_token or row.email != settings.google_workspace_email:
        raise ValueError("Workspace not connected")
    if row.access_token and row.expires_at and row.expires_at > datetime.now(UTC) + timedelta(minutes=2):
        token = decrypt_token(row.access_token)
    else:
        refresh = decrypt_token(row.refresh_token)
        tokens = await google.refresh_token(client, client_id=settings.google_client_id,
            client_secret=settings.google_client_secret, refresh=refresh)
        token = tokens["access_token"]
        row.access_token = encrypt_token(token)
        if tokens.get("refresh_token"):
            row.refresh_token = encrypt_token(tokens["refresh_token"])
        row.expires_at = datetime.now(UTC) + timedelta(seconds=int(tokens["expires_in"]))
    await db.commit()
    if not token:
        raise ValueError("Missing access token")
    return token
