"""Cookie session, CSRF and read-only auditor behaviour against a real database."""

import os

import pytest
from starlette.testclient import TestClient

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1 with DATABASE_URL pointed at Postgres",
)

OWNER = (
    os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@revivemydrive.co.uk"),
    os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe-RMD-2025!"),
)
AUDITOR = (os.environ.get("E2E_AUDITOR_EMAIL", ""), os.environ.get("E2E_AUDITOR_PASSWORD", ""))

# Admin-only POST; an empty body yields 422 only once authentication and CSRF have passed.
PROBE_POST = "/api/v1/crm/enquiries"


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return client.cookies.get("sc_csrf")


@requires_postgres
def test_cookie_session_requires_csrf_for_mutations():
    from app.main import app

    with TestClient(app) as client:
        csrf = _login(client, *OWNER)
        assert csrf
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.post(PROBE_POST, json={}).status_code == 403
        assert client.post(PROBE_POST, json={}, headers={"X-CSRF-Token": "wrong"}).status_code == 403
        assert client.post(PROBE_POST, json={}, headers={"X-CSRF-Token": csrf}).status_code == 422


@requires_postgres
def test_bearer_tokens_do_not_need_csrf():
    from app.main import app

    with TestClient(app) as client:
        token = client.post(
            "/api/v1/auth/token", data={"username": OWNER[0], "password": OWNER[1]}
        ).json()["access_token"]
        res = client.post(PROBE_POST, json={}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 422


@requires_postgres
def test_unknown_and_wrong_password_are_indistinguishable():
    from app.main import app

    with TestClient(app) as client:
        a = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x" * 20})
        b = client.post("/api/v1/auth/login", json={"email": OWNER[0], "password": "x" * 20})
        assert a.status_code == b.status_code == 401
        assert a.json() == b.json()


@requires_postgres
@pytest.mark.skipif(not AUDITOR[0], reason="E2E_AUDITOR_EMAIL/PASSWORD not set")
def test_auditor_is_read_only():
    from app.main import app

    with TestClient(app) as client:
        csrf = _login(client, *AUDITOR)
        me = client.get("/api/v1/auth/me").json()
        assert me["role"] == "auditor"
        for path in (
            "/api/v1/analytics/overview",
            "/api/v1/marketing/surfacecoat/overview",
            "/api/v1/finance/tax-centre/reserves",
        ):
            assert client.get(path).status_code == 200, path
        headers = {"X-CSRF-Token": csrf}
        assert client.post(PROBE_POST, json={}, headers=headers).status_code == 403
        assert client.post("/api/v1/assistant/chat", json={"message": "hi"}, headers=headers).status_code == 403
        assert client.get("/api/v1/finance/freeagent/authorize").status_code == 403
