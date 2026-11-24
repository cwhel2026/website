import pytest

from app.services.assistant_tools import tool_jobs_tomorrow, tool_pending_approvals


class EmptyResult:
    def all(self):
        return []


class EmptyScalars:
    def all(self):
        return []


class EmptyExec:
    def all(self):
        return []

    def scalars(self):
        return EmptyScalars()


class FakeSession:
    async def execute(self, stmt):
        return EmptyExec()


@pytest.mark.asyncio
async def test_jobs_tomorrow_empty():
    data = await tool_jobs_tomorrow(FakeSession())
    assert data["count"] == 0
    assert data["appointments"] == []


@pytest.mark.asyncio
async def test_pending_approvals_empty():
    data = await tool_pending_approvals(FakeSession())
    assert data["count"] == 0