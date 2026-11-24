import pytest

from app.services.assistant_brain import answer_question


class EmptyScalars:
    def all(self):
        return []


class EmptyExec:
    def all(self):
        return []

    def scalars(self):
        return EmptyScalars()

    def scalar(self):
        return 0

    def scalar_one_or_none(self):
        return None


class FakeSession:
    async def execute(self, stmt):
        return EmptyExec()


@pytest.mark.asyncio
async def test_assistant_tomorrow_question():
    reply, data = await answer_question(FakeSession(), "What jobs have I got tomorrow?")
    assert "Tomorrow" in reply
    assert "jobs_tomorrow" in data