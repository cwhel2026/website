import json
from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.jobs import Job, JobStatus
from app.models.finance import Invoice, InvoiceStatus
from app.models.agents import AgentProfile
from app.models.orchestration import AgentTask, TaskStatus
from app.services.materials_forecast import low_stock_alerts


MAX_NEW_TASKS_PER_RUN = 10


async def run_business_director_scan(db: AsyncSession) -> list[AgentTask]:
    """
    Deterministic coordinator: enqueue tasks for specialists based on real signals.
    Does not invoke LLMs or external APIs.
    """
    await db.execute(text("SELECT pg_advisory_xact_lock(52703105)"))
    profile = await db.scalar(select(AgentProfile).where(AgentProfile.slug == "business_director"))
    if profile and (profile.is_paused or profile.emergency_stop):
        return []
    created: list[AgentTask] = []

    pending_approvals = await db.scalar(
        select(func.count())
        .select_from(ApprovalRequest)
        .where(ApprovalRequest.status == ApprovalStatus.PENDING)
    )
    if pending_approvals and pending_approvals > 0:
        created.append(
            AgentTask(
                agent_slug="personal_assistant",
                action_key="review_approvals",
                title=f"Review {pending_approvals} pending approval(s)",
                payload_json=json.dumps({"count": pending_approvals}),
                priority=80,
            )
        )

    coat_pending = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.status.in_([JobStatus.RESTORATION_PENDING, JobStatus.PREPARATION_COMPLETED]))
    )
    if coat_pending and coat_pending > 0:
        created.append(
            AgentTask(
                agent_slug="scheduling",
                action_key="prioritise_coating",
                title=f"Prioritise {coat_pending} driveway(s) awaiting coating",
                payload_json=json.dumps({"count": coat_pending}),
                priority=90,
            )
        )

    alerts = await low_stock_alerts(db)
    for alert in alerts[:3]:
        created.append(
            AgentTask(
                agent_slug="inventory",
                action_key="replenish_stock",
                title=f"Low stock: {alert['sku']}",
                payload_json=json.dumps(alert),
                priority=70,
            )
        )

    overdue = await db.scalar(select(func.count()).select_from(Invoice).where(Invoice.status == InvoiceStatus.OVERDUE))
    if overdue:
        created.append(AgentTask(agent_slug="finance", action_key="review_overdue_invoices", title=f"Review {overdue} overdue invoice(s)", payload_json=json.dumps({"count": overdue}), priority=85))
    existing = (await db.execute(select(AgentTask).where(AgentTask.status.in_([TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.AWAITING_APPROVAL])))).scalars().all()
    keys = {task_identity(t) for t in existing}
    added = []
    for task in sorted(created, key=lambda t: t.priority, reverse=True):
        key = task_identity(task)
        if key in keys:
            continue
        db.add(task)
        added.append(task)
        keys.add(key)
        if len(added) >= MAX_NEW_TASKS_PER_RUN:
            break
    await db.flush()
    return added


def task_identity(task: AgentTask) -> tuple:
    payload = json.loads(task.payload_json or "{}")
    return task.agent_slug, task.action_key, payload.get("sku") if task.action_key == "replenish_stock" else None


async def list_open_tasks(db: AsyncSession, limit: int = 50) -> list[AgentTask]:
    result = await db.execute(
        select(AgentTask)
        .where(AgentTask.status.in_([TaskStatus.QUEUED, TaskStatus.AWAITING_APPROVAL]))
        .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def complete_task(db: AsyncSession, task_id, result: dict | None = None) -> AgentTask | None:
    from uuid import UUID

    task = await db.get(AgentTask, UUID(str(task_id)) if isinstance(task_id, str) else task_id)
    if task is None:
        return None
    if task.status != TaskStatus.QUEUED:
        return task
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(UTC)
    task.result_json = json.dumps(result or {"ok": True})
    return task