from datetime import datetime, UTC
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking_payment import BookingDeposit
from app.models.finance import Invoice, InvoiceStatus
from app.models.jobs import Job, JobStatus, Appointment, AppointmentStatus, AppointmentType

LONDON = ZoneInfo("Europe/London")


async def confirm_paid_booking(db: AsyncSession, job_id) -> list[Appointment]:
    """Local transaction only. Caller owns commit and durable notification delivery."""
    job = await db.get(Job, job_id, with_for_update=True)
    if not job or job.status not in (JobStatus.DRAFT, JobStatus.AWAITING_PREP_BOOKING,
                                     JobStatus.BOOKED, JobStatus.PREPARATION_SCHEDULED):
        raise ValueError("Job is not eligible for booking confirmation")
    deposit = await db.scalar(select(BookingDeposit).where(
        BookingDeposit.job_id == job_id).with_for_update())
    invoice = await db.get(Invoice, deposit.invoice_id, with_for_update=True) if deposit else None
    if (not invoice or invoice.status != InvoiceStatus.PAID
            or invoice.customer_id != job.customer_id or invoice.job_id != job.id
            or invoice.amount_paid_gbp != invoice.total_inc_vat_gbp
            or invoice.total_inc_vat_gbp * 100 != deposit.amount_pence):
        raise ValueError("A fully settled deposit invoice is required")
    appointments = list(await db.scalars(select(Appointment).where(
        Appointment.job_id == job_id,
        Appointment.status.in_((AppointmentStatus.PROVISIONAL, AppointmentStatus.CONFIRMED))
    ).order_by(Appointment.scheduled_start).with_for_update()))
    eligible = [a for a in appointments if a.appointment_type != AppointmentType.COATING]
    if not eligible:
        raise ValueError("A provisional preparation or service appointment is required")
    for appointment in eligible:
        if appointment.scheduled_start <= datetime.now(UTC) or appointment.scheduled_end <= appointment.scheduled_start:
            raise ValueError("Appointment must have a valid future time")
    for appointment in eligible:
        appointment.status = AppointmentStatus.CONFIRMED
    job.status = JobStatus.PREPARATION_SCHEDULED if job.requires_two_stage else JobStatus.BOOKED
    return eligible


def calendar_payload(job: Job, appointment: Appointment) -> dict:
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise ValueError("Only confirmed appointments may be published")
    return {
        "id": appointment.id.hex,
        "summary": f"SurfaceCoat {job.reference}: {appointment.appointment_type.value}",
        "location": appointment.postcode or "",
        "start": {"dateTime": appointment.scheduled_start.astimezone(LONDON).isoformat(),
                  "timeZone": "Europe/London"},
        "end": {"dateTime": appointment.scheduled_end.astimezone(LONDON).isoformat(),
                "timeZone": "Europe/London"},
    }
