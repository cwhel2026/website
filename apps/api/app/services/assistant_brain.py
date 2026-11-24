"""Backward-compatible entrypoint — delegates to tool-enabled orchestrator."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.orchestrator import answer_question as orchestrate_answer


async def answer_question(db: AsyncSession, question: str) -> tuple[str, dict[str, Any]]:
    reply, tool_data, _provider = await orchestrate_answer(db, question)
    return reply, tool_data