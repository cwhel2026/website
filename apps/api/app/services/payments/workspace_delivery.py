"""Delivery adapter for booking notifications; scheduler integration is separate."""
import json
from datetime import UTC, datetime

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.models.notifications import NotificationOutbox, OutboxStatus
from app.services.google_workspace import WorkspaceClient
from app.services.workspace_connection import access_token


async def deliver_booking_notification(session_factory, notification_id) -> str:
    settings = get_settings()
    if settings.global_emergency_stop or not settings.workspace_booking_delivery_enabled:
        return "disabled"
    async with httpx.AsyncClient(timeout=20) as http:
        async with session_factory() as db:
            token = await access_token(db, http)
        client = WorkspaceClient(http, token)
        async with session_factory() as db:
            row = await db.scalar(select(NotificationOutbox).where(
                NotificationOutbox.id == notification_id,
                NotificationOutbox.category == "booking_confirmation",
                NotificationOutbox.channel.in_(("workspace_email", "workspace_calendar")),
                NotificationOutbox.status == OutboxStatus.PENDING,
            ).with_for_update(skip_locked=True))
            if not row:
                return "not_pending"
            if row.attempts >= row.max_attempts:
                row.status = OutboxStatus.FAILED
                await db.commit()
                return "failed"
            payload = json.loads(row.payload_json)
            channel = row.channel
            row.attempts += 1
            row.status = OutboxStatus.SENDING
            await db.commit()
            try:
                if channel == "workspace_email":
                    await client.send_email(settings.google_workspace_email, payload["recipient"],
                                            payload["subject"], payload["body"])
                else:
                    await client.publish_booking_event(payload)
            except (httpx.HTTPError, ValueError, KeyError):
                # Gmail does not guarantee idempotency: uncertain sends need human review.
                row.status = (OutboxStatus.PENDING if channel == "workspace_calendar"
                              and row.attempts < row.max_attempts else OutboxStatus.FAILED)
                row.last_error = "Workspace delivery failed; verify provider before retrying"
            else:
                row.status = OutboxStatus.DELIVERED
                row.delivered_at = datetime.now(UTC)
                row.last_error = None
            result = row.status.value
            await db.commit()
            return result
