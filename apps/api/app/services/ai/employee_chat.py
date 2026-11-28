"""Owner-only employee chat, scoped history and fail-closed provider access."""
from sqlalchemy import select
from app.models.agents import AgentProfile
from app.models.notifications import TelegramConversationMessage
from app.services.ai.employees import EMPLOYEES
from app.services.ai.providers.openai_provider import chat_with_openai


async def employee_reply(db, chat_id, slug, question, request_id=None):
    name = EMPLOYEES[slug][0]
    profile = (await db.execute(select(AgentProfile).where(AgentProfile.slug == slug))).scalar_one_or_none()
    if profile and (profile.is_paused or profile.emergency_stop):
        return f"{name}: This department is paused."
    rows = (await db.execute(select(TelegramConversationMessage).where(
        TelegramConversationMessage.chat_id == chat_id,
        TelegramConversationMessage.agent_slug == slug,
    ).order_by(TelegramConversationMessage.created_at.desc()).limit(12))).scalars().all()
    history = [{"role": "user" if row.direction == "inbound" else "assistant", "content": row.body[:1500]} for row in reversed(rows)]
    try:
        async with db.begin_nested():
            reply, _, _ = await chat_with_openai(db, question, agent_slug=slug, history=history, execution_context={"chat_id": chat_id, "request_id": request_id} if request_id is not None else None)
    except Exception:
        reply = "My AI service is currently unavailable. No business action has been taken."
    db.add(TelegramConversationMessage(chat_id=chat_id, agent_slug=slug, direction="inbound", body=question))
    db.add(TelegramConversationMessage(chat_id=chat_id, agent_slug=slug, direction="outbound", body=reply[:3500]))
    return f"{name}: {reply[:3500]}"
