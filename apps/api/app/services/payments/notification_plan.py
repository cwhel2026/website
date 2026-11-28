"""Build deterministic delivery tasks for a durable outbox."""
from app.services.payments.confirmation import calendar_payload
from app.services.payments.messages import booking_confirmation


def booking_notification_plan(job, appointments, *, customer_name: str,
                              recipient: str, address: str, service: str) -> list[dict]:
    if not recipient or "@" not in recipient or any(c in recipient for c in "\r\n,;"):
        raise ValueError("A single customer email address is required")
    subject, body = booking_confirmation(customer_name, job.reference, address,
                                          service, appointments, two_stage=job.requires_two_stage)
    tasks = [{
        "key": f"booking-confirmation:{job.id.hex}",
        "kind": "workspace_email",
        "payload": {"recipient": recipient, "subject": subject, "body": body},
    }]
    for appointment in appointments:
        tasks.append({
            "key": f"booking-calendar:{appointment.id.hex}",
            "kind": "workspace_calendar",
            "payload": calendar_payload(job, appointment),
        })
    return tasks


async def enqueue_booking_notifications(db, job, appointments, **customer_details) -> None:
    import json
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert
    from app.models.notifications import NotificationOutbox, NotificationPriority, OutboxStatus

    for task in booking_notification_plan(job, appointments, **customer_details):
        await db.execute(insert(NotificationOutbox).values(
            dedupe_key=task["key"],
            channel=task["kind"],
            category="booking_confirmation",
            priority=NotificationPriority.NORMAL,
            title="Booking confirmation delivery",
            body="Booking notification",
            payload_json=json.dumps(task["payload"]),
            status=OutboxStatus.PENDING,
            attempts=0,
            max_attempts=5,
        ).on_conflict_do_nothing(
            index_elements=["dedupe_key"],
            index_where=text("dedupe_key IS NOT NULL"),
        ))
    # Caller commits alongside the booking state transition.
