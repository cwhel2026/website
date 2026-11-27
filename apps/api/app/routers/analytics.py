from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.analytics_service import build_analytics_snapshot, regional_analytics
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = 30,
) -> dict:
    snap = await build_analytics_snapshot(db, days)
    return snap.__dict__


@router.get("/regional")
async def regional(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return await regional_analytics(db)

@router.get("/command-centre")
async def command_centre(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from datetime import UTC, datetime, timedelta
    from zoneinfo import ZoneInfo
    from sqlalchemy import func, select
    from app.models.approvals import ApprovalRequest, ApprovalStatus
    from app.models.crm import Customer
    from app.models.jobs import Appointment, AppointmentStatus, Job, JobStatus
    from app.models.quotation import Quotation, QuotationStatus
    from app.models.finance import Invoice, InvoiceStatus
    from app.models.orchestration import AgentTask, TaskStatus

    now = datetime.now(UTC)
    today = now.astimezone(ZoneInfo("Europe/London")).date()
    async def count(model, *conditions):
        return await db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0

    active_jobs = (Job.status.notin_((JobStatus.COMPLETED, JobStatus.CANCELLED)), Customer.is_test.is_(False))
    visits = select(Appointment, Job.reference).join(Job, Appointment.job_id == Job.id).join(Customer, Job.customer_id == Customer.id).where(*active_jobs, Appointment.status == AppointmentStatus.CONFIRMED, Appointment.scheduled_start >= now)
    upcoming = (await db.execute(visits.order_by(Appointment.scheduled_start).limit(5))).all()
    pending_coat = await db.scalar(select(func.count()).select_from(Job).join(Customer, Job.customer_id == Customer.id).where(*active_jobs, Job.requires_two_stage.is_(True), Job.preparation_completed_at.is_not(None), Job.coating_completed_at.is_(None), Job.seven_day_target_date <= today + timedelta(days=2))) or 0
    outstanding = await db.scalar(select(func.coalesce(func.sum(Invoice.total_inc_vat_gbp - Invoice.amount_paid_gbp), 0)).join(Customer, Invoice.customer_id == Customer.id).where(Customer.is_test.is_(False), Invoice.status.in_((InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE)), Invoice.total_inc_vat_gbp > Invoice.amount_paid_gbp))
    tasks = (await db.execute(select(AgentTask).where(AgentTask.status.in_((TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.AWAITING_APPROVAL))).order_by(AgentTask.priority.desc(), AgentTask.created_at).limit(5))).scalars().all()
    return {
        "as_of": now.isoformat(),
        "open_quotes": await count(Quotation, Quotation.is_test.is_(False), Quotation.status.in_((QuotationStatus.DRAFT, QuotationStatus.PROVISIONAL, QuotationStatus.PENDING_APPROVAL, QuotationStatus.SENT))),
        "pending_approvals": await count(ApprovalRequest, ApprovalRequest.status == ApprovalStatus.PENDING),
        "coating_due_within_two_days": pending_coat,
        "outstanding_invoice_gbp": str(outstanding or 0),
        "upcoming_visits": [{"id": str(a.id), "reference": ref, "start": a.scheduled_start.isoformat(), "type": a.appointment_type.value, "weather_suitable": a.weather_suitable} for a, ref in upcoming],
        "director_tasks": [{"id": str(t.id), "title": t.title, "priority": t.priority} for t in tasks],
    }
