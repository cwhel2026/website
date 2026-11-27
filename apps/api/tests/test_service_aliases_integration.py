import os

import pytest

from app.database import SessionLocal
from app.services.quotation_persist import load_active_service

requires_postgres = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1",
)


@requires_postgres
@pytest.mark.asyncio
async def test_load_active_service_resolves_marketing_slug():
    async with SessionLocal() as db:
        service = await load_active_service(db, "tarmac-restoration")
        assert service.slug == "tarmac-driveway-restoration"
        assert service.is_active is True