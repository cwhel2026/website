"""Process one explicitly delegated owner task per worker invocation."""
import json
from sqlalchemy import select
from app.models.orchestration import AgentTask, TaskStatus
from app.models.agents import AgentProfile
from app.services.ai.providers.openai_provider import chat_with_openai
from app.services.notifications.outbox import enqueue_notification


async def run_next_owner_task(db):
    from app.services.ai.execution import run_next_employee_work
    execution = await run_next_employee_work(db)
    if execution.get("processed") or execution.get("failed_attempt"):
        return execution
    task = await db.scalar(select(AgentTask).join(AgentProfile, AgentProfile.slug == AgentTask.agent_slug).where(
        AgentTask.action_key == "owner_manual_task",
        AgentTask.status == TaskStatus.QUEUED,
        AgentTask.result_json.is_(None),
        AgentTask.iteration_count < 3,
        AgentProfile.is_paused.is_(False),
        AgentProfile.emergency_stop.is_(False),
    ).order_by(AgentTask.priority.desc(), AgentTask.created_at).limit(1).with_for_update(of=AgentTask, skip_locked=True))
    if task is None:
        return {"processed": 0}
    task.iteration_count += 1
    try:
        async with db.begin_nested():
            reply, _, provider = await chat_with_openai(db, "Prepare a read-only draft work report. No external actions. Owner task: " + task.title, agent_slug=task.agent_slug)
            task.result_json = json.dumps({"draft_report": reply, "provider": provider, "owner_review_required": True})
            await enqueue_notification(db, channel="telegram", title="Employee work ready for review", body=f"{task.title}\nReference: {task.id}\n{reply[:3000]}", category="assistant_reply", dedupe_key=f"employee-report:{task.id}", priority="normal", payload={"reply_chat_id": int(task.assigned_by.split(":")[1])})
    except Exception:
        if task.iteration_count >= 3:
            task.status = TaskStatus.FAILED
            task.result_json = json.dumps({"error": "Report generation failed after three attempts"})
        await db.commit()
        return {"processed": 0, "failed_attempt": True}
    await db.commit()
    return {"processed": 1}
