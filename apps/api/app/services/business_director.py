import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.jobs import Job, JobStatus
from app.models.orchestration import AgentTask, TaskStatus
from app.services.materials_forecast import low_stock_alerts


MAX_NEW_TASKS_PER_RUN = 10


async def run_business_director_scan(db: AsyncSession) -> list[AgentTask]:
    """
    Deterministic coordinator: enqueue tasks for specialists based on real signals.
    Does not invoke LLMs or external APIs.
    """
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

    for task in created[:MAX_NEW_TASKS_PER_RUN]:
        db.add(task)
    await db.flush()
    return created


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
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(UTC)
    task.result_json = json.dumps(result or {"ok": True})
    return task