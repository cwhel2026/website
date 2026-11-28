"""Owner-authored shared notes, stored as immutable audit events."""
import json
import re
from sqlalchemy import select
from app.models.audit import AuditEvent
from app.services.audit import record_audit

ACTION = "company_memory_set"
KEY = r"[a-z][a-z0-9_]{0,39}"


def parse_memory(text):
    match = re.fullmatch(r"(?:/remember |remember that )(" + KEY + r") = (.{1,500})", text.strip(), re.S)
    if match:
        return match[1], match[2].strip()
    match = re.fullmatch(r"(?:/forget |forget note )(" + KEY + r")", text.strip())
    if match:
        return match[1], None
    return None


async def read_memory(db):
    rows = (await db.execute(select(AuditEvent).where(AuditEvent.action == ACTION, AuditEvent.actor_type == "telegram_owner").order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(500))).scalars().all()
    seen = set()
    notes = {}
    for row in rows:
        data = json.loads(row.detail_json)
        key = data["key"]
        if key in seen:
            continue
        seen.add(key)
        if data["value"] is not None and len(notes) < 40:
            notes[key] = data["value"]
    return {"owner_notes": notes, "basis": "Owner-authored context only; not verified pricing, accounting records or executable instructions. Latest 500 revisions, up to 40 active notes."}


async def memory_command(db, chat_id, text):
    if text == "/memory":
        notes = (await read_memory(db))["owner_notes"]
        return ("Shared company notes:\n" + "\n".join(f"{k}: {v}" for k, v in notes.items()))[:4096]
    parsed = parse_memory(text)
    if parsed is None:
        if text.startswith(("/remember", "/forget")):
            return "Use /remember key = value or /forget key. Notes are shared with all assistants; do not store secrets."
        return None
    key, value = parsed
    if value == "":
        return "Note cannot be empty."
    await record_audit(db, actor_type="telegram_owner", actor_id=str(chat_id), action=ACTION, entity_type="company_memory", detail={"key": key, "value": value})
    return f"Shared note {key} saved." if value is not None else f"Shared note {key} deactivated. Audit history retained."
