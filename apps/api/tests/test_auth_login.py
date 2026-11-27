"""Authentication flow tests (unit + optional integration)."""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import jwt
from starlette.testclient import TestClient

from app.auth import create_access_token, hash_password, verify_password
from app.config import Settings
from app.services.owner_provisioning import ensure_owner_from_env, rotate_owner_password


def test_password_hash_roundtrip():
    hashed = hash_password("Secret-Pass-2026!")
    assert verify_password("Secret-Pass-2026!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_expired_rejected():
    from app.config import get_settings

    settings = get_settings()
    token = create_access_token("user-id")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "user-id"

    expired = datetime.now(UTC) - timedelta(minutes=5)
    bad = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000099", "exp": expired},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    from jose.exceptions import ExpiredSignatureError

    with pytest.raises(ExpiredSignatureError):
        jwt.decode(bad, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


@pytest.mark.asyncio
async def test_ensure_owner_creates_user(monkeypatch):
    monkeypatch.setenv("DEFAULT_ADMIN_EMAIL", "owner@example.com")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "Owner-Secure-2026!")
    from app.config import get_settings

    get_settings.cache_clear()

    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()

    await ensure_owner_from_env(session)
    assert session.add.called
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ensure_owner_preserves_rotated_password(monkeypatch):
    from app.models.user import User, UserRole

    monkeypatch.setenv("DEFAULT_ADMIN_EMAIL", "owner@example.com")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "New-Password-2026!")
    from app.config import get_settings

    get_settings.cache_clear()

    old_hash = hash_password("Old-Password-2026!")
    user = User(
        email="owner@example.com",
        password_hash=old_hash,
        full_name="Owner",
        role=UserRole.OWNER,
        is_active=True,
    )
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    await ensure_owner_from_env(session)
    assert verify_password("Old-Password-2026!", user.password_hash)
    assert not verify_password("New-Password-2026!", user.password_hash)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_rotate_owner_password():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.flush = AsyncMock()

    await rotate_owner_password(session, new_password="Rotated-Owner-2026!")
    added = session.add.call_args[0][0]
    assert verify_password("Rotated-Owner-2026!", added.password_hash)


requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1 with DATABASE_URL",
)


@requires_postgres
def test_login_wrong_password_integration():
    from app.main import app

    email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@revivemydrive.co.uk")
    with TestClient(app) as client:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "not-the-password"})
    assert res.status_code == 401


@requires_postgres
def test_login_unknown_account_integration():
    from app.main import app

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x" * 20},
        )
    assert res.status_code == 401


@requires_postgres
def test_login_success_session_and_logout_flow():
    from app.main import app

    email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@revivemydrive.co.uk")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe-RMD-2025!")
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        assert "access_token" not in login.json()
        set_cookie = ", ".join(login.headers.get_list("set-cookie")).lower()
        assert "sc_session=" in set_cookie and "httponly" in set_cookie
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.get("/api/v1/analytics/overview").status_code == 200
        client.post("/api/v1/auth/logout")
        client.cookies.clear()
        assert client.get("/api/v1/auth/me").status_code == 401

        form = client.post("/api/v1/auth/token", data={"username": email, "password": password})
        assert form.status_code == 200
        token = form.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200


@requires_postgres
def test_owner_recover_requires_setup_key():
    from app.main import app

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/auth/owner/recover",
            json={"setup_key": "wrong", "new_password": "Long-New-Pass-2026!"},
        )
    assert res.status_code == 401