"""Owner-only local task management; no external execution."""
import json
import re
from uuid import UUID
from sqlalchemy import select
from app.models.orchestration import AgentTask, TaskStatus
from app.services.business_director import list_open_tasks, complete_task
from app.services.audit import record_audit

AGENTS = {"alex": "personal_assistant", "olivia": "marketing", "arthur": "finance"}


def parse_task(text):
    match = re.fullmatch(r"(?:/task |assign to )(alex|olivia|arthur)[: ]+(.{1,240})", text.strip(), re.I)
    if match and match[2].strip():
        return AGENTS[match[1].lower()], match[2].strip()
    return None


async def task_command(db, chat_id, text):
    if text.lower() == "/tasks":
        tasks = await list_open_tasks(db, 15)
        return ("Open tasks:\n" + "\n".join(f"{t.title} ({t.agent_slug}, {t.status.value})\n{t.id}" for t in tasks))[:4096] if tasks else "No open tasks."
    parsed = parse_task(text)
    if parsed:
        agent, title = parsed
        task = AgentTask(agent_slug=agent, assigned_by=f"telegram:{chat_id}", action_key="owner_manual_task", title=title, payload_json=json.dumps({"manual_only": True}), priority=50)
        db.add(task)
        await db.flush()
        await record_audit(db, actor_type="telegram_owner", actor_id=str(chat_id), action="task_created", entity_type="agent_task", entity_id=task.id)
        return f"Task recorded for {agent}: {title}\nReference: {task.id}\nQueued for review; no external action executed."
    run = re.fullmatch(r"/work ([0-9a-fA-F-]{36})", text.strip())
    if run:
        try:
            ident = UUID(run[1])
        except ValueError:
            return "Invalid task reference."
        task = (await db.execute(select(AgentTask).where(AgentTask.id == ident).with_for_update())).scalar_one_or_none()
        if not task or task.action_key != "owner_manual_task" or task.assigned_by != f"telegram:{chat_id}" or task.status != TaskStatus.QUEUED:
            return "No matching queued owner task."
        from app.models.agents import AgentProfile
        profile = await db.scalar(select(AgentProfile).where(AgentProfile.slug == task.agent_slug))
        if not profile or profile.is_paused or profile.emergency_stop:
            return "Employee unavailable or paused."
        from app.services.ai.providers.openai_provider import chat_with_openai
        reply, _, provider = await chat_with_openai(db, "Prepare a read-only work report for this owner task. Do not execute external actions or claim completion of external work. Task: " + task.title, agent_slug=task.agent_slug)
        task.result_json = json.dumps({"draft_report": reply, "provider": provider, "owner_review_required": True})
        await record_audit(db, actor_type="telegram_owner", actor_id=str(chat_id), action="task_report_generated", entity_type="agent_task", entity_id=ident)
        return ("Draft work report (task remains queued for owner review):\\n" + reply)[:4096]
    match = re.fullmatch(r"/done ([0-9a-fA-F-]{36})", text.strip())
    if not match:
        return None
    try:
        ident = UUID(match[1])
    except ValueError:
        return "Invalid task reference."
    task = (await db.execute(select(AgentTask).where(AgentTask.id == ident).with_for_update())).scalar_one_or_none()
    if not task or task.action_key != "owner_manual_task" or task.assigned_by != f"telegram:{chat_id}" or task.status != TaskStatus.QUEUED:
        return "No matching queued owner task. Approval and automated tasks cannot be completed here."
    await complete_task(db, ident, {"owner_marked_complete": True})
    await record_audit(db, actor_type="telegram_owner", actor_id=str(chat_id), action="task_completed", entity_type="agent_task", entity_id=ident)
    return f"Marked complete: {task.title}"
