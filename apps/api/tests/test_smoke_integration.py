import os

import pytest
from starlette.testclient import TestClient

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1 with DATABASE_URL pointed at Postgres",
)


@requires_postgres
def test_ready_and_territories_after_seed():
    from app.main import app

    with TestClient(app) as client:
        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] == "ok"
        territories = client.get("/api/v1/territories")
        assert territories.status_code == 200
        data = territories.json()
        assert len(data) >= 9
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@revivemydrive.co.uk"),
                "password": os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe-RMD-2025!"),
            },
        )
        assert login.status_code == 200
        assert "access_token" not in login.json()
        overview = client.get("/api/v1/analytics/overview")
        assert overview.status_code == 200
        marketing = client.get("/api/v1/marketing/surfacecoat/overview")
        assert marketing.status_code == 200, marketing.text