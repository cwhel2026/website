import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.auth import hash_password
from app.routers import auth as auth_router


class _Result:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class _Db:
    def __init__(self, user):
        self._user = user

    async def execute(self, _stmt):
        return _Result(self._user)


def _user(password: str):
    return SimpleNamespace(email="owner@example.com", password_hash=hash_password(password), is_active=True)


@pytest.mark.parametrize("environment,expect_refused", [("production", True), ("development", False)])
def test_factory_default_password(monkeypatch, environment, expect_refused):
    monkeypatch.setattr(auth_router, "get_settings", lambda: SimpleNamespace(environment=environment))
    db = _Db(_user("ChangeMe-RMD-2025!"))
    if expect_refused:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(auth_router._authenticate(db, "owner@example.com", "ChangeMe-RMD-2025!"))
        assert exc.value.status_code == 403
    else:
        assert asyncio.run(auth_router._authenticate(db, "owner@example.com", "ChangeMe-RMD-2025!"))


def test_unique_password_allowed_in_production(monkeypatch):
    monkeypatch.setattr(auth_router, "get_settings", lambda: SimpleNamespace(environment="production"))
    db = _Db(_user("a-unique-owner-password-123"))
    assert asyncio.run(auth_router._authenticate(db, "owner@example.com", "a-unique-owner-password-123"))
