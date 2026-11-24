import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


async def record_audit(
    db: AsyncSession,
    *,
    actor_type: str,
    actor_id: str | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | UUID | None = None,
    detail: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        detail_json=json.dumps(detail or {}),
    )
    db.add(event)
    await db.flush()
    return event