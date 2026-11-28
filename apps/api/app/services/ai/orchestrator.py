from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.ai.deterministic_reply import answer_deterministic
from app.services.ai.providers.openai_provider import chat_with_openai

settings = get_settings()


async def answer_question(
    db: AsyncSession,
    question: str,
    *,
    agent_slug: str = "personal_assistant",
) -> tuple[str, dict[str, Any], str]:
    """
    Tool-enabled assistant. OpenAI when configured and within spend limits;
    otherwise deterministic tool routing (no fabricated data).
    """
    provider = settings.ai_provider.lower()
    if provider in {"openai", "auto"} and settings.openai_api_key:
        try:
            reply, tool_data, used = await chat_with_openai(db, question, agent_slug=agent_slug)
            return reply, tool_data, used
        except Exception:
            fallback, tool_data = await answer_deterministic(db, question)
            return (
                f"{fallback}\n\n(AI provider unavailable. Showing tool-backed summary.)",
                tool_data,
                "deterministic_fallback",
            )

    if provider == "claude" and settings.anthropic_api_key:
        # Adapter placeholder — falls back until HTTP integration is approved.
        reply, tool_data = await answer_deterministic(db, question)
        return (
            reply + "\n\n(Claude adapter not yet enabled — using authorised tools only.)",
            tool_data,
            "deterministic_tools",
        )

    reply, tool_data = await answer_deterministic(db, question)
    return reply, tool_data, "deterministic_tools"