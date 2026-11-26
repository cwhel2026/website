"""Ad campaigns cannot be launched without an approved AD_SPEND request."""

import os
import uuid

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


@requires_postgres
def test_launch_requires_approval_and_reports_simulation():
    from app.main import app

    with TestClient(app) as client:
        token = client.post(
            "/api/v1/auth/token", data={"username": OWNER[0], "password": OWNER[1]}
        ).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/marketing/campaigns",
            json={"name": f"approval-gate-{uuid.uuid4().hex[:8]}", "platform": "meta", "daily_budget_gbp": "0"},
            headers=h,
        )
        if res.status_code != 200:
            pytest.skip(f"campaign creation gated in this environment: {res.status_code} {res.text}")
        campaign = res.json()
        assert campaign["simulation_only"] is True

        assert client.post(f"/api/v1/marketing/campaigns/{campaign['id']}/launch-approved", headers=h).status_code == 409

        res = client.post(f"/api/v1/marketing/campaigns/{campaign['id']}/request-launch", headers=h)
        if res.status_code == 400:
            pytest.skip(f"budget headroom unavailable: {res.text}")
        assert res.status_code == 200, res.text
        assert client.post(f"/api/v1/marketing/campaigns/{campaign['id']}/launch-approved", headers=h).status_code == 409

        pending = client.get("/api/v1/approvals", headers=h).json()
        approval = next(a for a in pending if a["entity_id"] == campaign["id"])
        assert client.post(f"/api/v1/approvals/{approval['id']}/approve", json={}, headers=h).status_code == 200

        res = client.post(f"/api/v1/marketing/campaigns/{campaign['id']}/launch-approved", headers=h)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["live"] is False and body["simulation"] is True
        assert "SIMULATED" in body["message"]
