import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approvals import ApprovalRequest, ApprovalStatus
from app.models.jobs import Job, JobStatus, Appointment, AppointmentStatus
from app.models.crm import Enquiry, OwnerFollowUp
from app.models.finance import Invoice, InvoiceStatus, BankTransaction
from app.models.quotation import Quotation, QuotationStatus
from app.models.marketing_ops import CommercialProspect, OutreachMessage, OutreachMessageStatus
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
    if not profile or profile.is_paused or profile.emergency_stop:
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

    followups = await db.scalar(
        select(func.count()).select_from(OwnerFollowUp)
        .join(Enquiry, Enquiry.id == OwnerFollowUp.enquiry_id)
        .where(OwnerFollowUp.status == "open", OwnerFollowUp.due_at <= datetime.now(UTC), Enquiry.is_test.is_(False))
    )
    if followups:
        created.append(AgentTask(agent_slug="personal_assistant", action_key="review_due_followups", title=f"Review {followups} due customer follow-up(s)", payload_json=json.dumps({"count": followups}), priority=85))

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
    signals = await director_signals(db)
    for key, count in signals.items():
        if count and key in SIGNAL_ACTIONS:
            agent, title, priority = SIGNAL_ACTIONS[key]
            created.append(AgentTask(agent_slug=agent, action_key=key, title=f"{title}: {count}", payload_json=json.dumps({"count": count}), priority=priority))
    existing = (await db.execute(select(AgentTask).where(AgentTask.status.in_([TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.AWAITING_APPROVAL])))).scalars().all()
    await reconcile_signal_tasks(db, existing, signals)
    keys = {task_identity(t) for t in existing if t.status != TaskStatus.CANCELLED}
    profiles = {p.slug: p for p in (await db.execute(select(AgentProfile))).scalars().all()}
    added = []
    for task in sorted(created, key=lambda t: t.priority, reverse=True):
        specialist = profiles.get(task.agent_slug)
        if specialist and (specialist.is_paused or specialist.emergency_stop):
            continue
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
    try:
        payload = json.loads(task.payload_json or "{}")
    except (ValueError, TypeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
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

    task = await db.get(AgentTask, UUID(str(task_id)) if isinstance(task_id, str) else task_id, with_for_update=True)
    if task is None:
        return None
    if task.status != TaskStatus.QUEUED:
        return task
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(UTC)
    task.result_json = json.dumps(result or {"ok": True})
    return task

SIGNAL_ACTIONS = {
    "coating_deadline_risk": ("scheduling", "Review coating deadlines", 95),
    "weather_delayed": ("weather", "Review weather-delayed visits", 92),
    "unreconciled_bank": ("finance", "Review unreconciled bank transactions", 75),
    "pending_quotes": ("customer_service", "Review provisional quotations", 65),
    "outreach_review": ("marketing", "Review outreach drafts", 60),
}


async def director_signals(db: AsyncSession) -> dict[str, int]:
    """Read-only cross-department signals; counts are local records, not forecasts."""
    today = datetime.now(ZoneInfo("Europe/London")).date()
    from datetime import timedelta
    queries = {
        "coating_deadline_risk": select(func.count()).select_from(Job).where(Job.status.in_([JobStatus.RESTORATION_PENDING, JobStatus.PREPARATION_COMPLETED, JobStatus.COATING_SCHEDULED]), Job.seven_day_target_date <= today + timedelta(days=2)),
        "weather_delayed": select(func.count()).select_from(Appointment).join(Job).where(Appointment.status == AppointmentStatus.WEATHER_DELAYED, Job.status.notin_([JobStatus.COMPLETED, JobStatus.CANCELLED])),
        "unreconciled_bank": select(func.count()).select_from(BankTransaction).where(BankTransaction.is_duplicate.is_(False), BankTransaction.is_reconciled.is_(False)),
        "pending_quotes": select(func.count()).select_from(Quotation).where(Quotation.is_test.is_(False), Quotation.status == QuotationStatus.PROVISIONAL),
        "outreach_review": select(func.count()).select_from(OutreachMessage).join(CommercialProspect).where(OutreachMessage.status == OutreachMessageStatus.PENDING_APPROVAL, CommercialProspect.opt_out.is_(False)),
    }
    return {key: int(await db.scalar(query) or 0) for key, query in queries.items()}


async def reconcile_signal_tasks(db, tasks, signals):
    """Refresh queued recommendations; never cancel running or approval tasks."""
    for task in tasks:
        if task.status != TaskStatus.QUEUED or task.action_key not in SIGNAL_ACTIONS:
            continue
        count = signals.get(task.action_key)
        if count is None:
            continue
        locked = await db.get(AgentTask, task.id, with_for_update=True, populate_existing=True)
        if locked is None or locked.status != TaskStatus.QUEUED:
            continue
        if count == 0:
            locked.status = TaskStatus.CANCELLED
            locked.completed_at = datetime.now(UTC)
            locked.result_json = json.dumps({"reason": "signal_resolved"})
        else:
            locked.payload_json = json.dumps({"count": count})
            locked.title = f"{SIGNAL_ACTIONS[locked.action_key][1]}: {count}"


async def director_target_review(db, monthly_target):
    """Compare owner-supplied target with recorded eligible invoice payments."""
    from datetime import time
    from decimal import Decimal
    from app.models.finance import Payment
    from app.models.crm import Customer
    london = ZoneInfo("Europe/London")
    now = datetime.now(london)
    start = datetime.combine(now.date().replace(day=1), time.min, tzinfo=london)
    amount = await db.scalar(select(func.coalesce(func.sum(Payment.amount_gbp), 0)).select_from(Payment).join(Invoice, Payment.invoice_id == Invoice.id).join(Customer, Invoice.customer_id == Customer.id).outerjoin(Quotation, Invoice.quotation_id == Quotation.id).where(Customer.is_test.is_(False), (Quotation.id.is_(None) | Quotation.is_test.is_(False)), Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.VOID]), Payment.paid_at >= start, Payment.paid_at <= now))
    recorded = Decimal(str(amount or 0))
    return {"monthly_target_gbp": str(monthly_target), "recorded_payments_gbp": str(recorded), "remaining_gbp": str(max(Decimal("0"), monthly_target-recorded)), "basis": "recorded_invoice_payments_not_verified_bank_cash"}
