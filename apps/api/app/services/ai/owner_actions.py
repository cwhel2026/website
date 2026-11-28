"""Explicit owner-confirmed local budget changes; never calls ad platforms."""
import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from app.models.approvals import ApprovalRequest, ApprovalStatus, ApprovalType
from app.models.marketing_ops import MarketingBudgetPolicy
from app.services.audit import record_audit

FIELDS = {"facebook weekly": "meta_weekly_budget_gbp", "marketing weekly": "weekly_limit_gbp", "marketing daily": "daily_limit_gbp", "marketing monthly": "monthly_limit_gbp"}


def parse_budget(text):
    m = re.fullmatch(r"(?:olivia[, :]+|alex[, :]+)?(?:set|change) (?:our )?(facebook weekly|marketing weekly|marketing daily|marketing monthly) budget to £?(\d{1,6}(?:\.\d{1,2})?)", text.strip(), re.I)
    if not m:
        return None
    value = Decimal(m[2])
    if value <= 0 or value > 100000:
        return None
    return FIELDS[m[1].lower()], value


async def owner_action(db, chat_id, text):
    proposal = parse_budget(text)
    confirmation = re.fullmatch(r"/(confirm|cancel) ([0-9a-fA-F-]{36})", text.strip())
    if not proposal and not confirmation:
        return None
    actor = f"telegram:{chat_id}"
    if proposal:
        field, value = proposal
        policy = (await db.execute(select(MarketingBudgetPolicy).limit(1).with_for_update())).scalar_one_or_none()
        if not policy:
            return "No marketing budget policy configured. Set it up first."
        old = getattr(policy, field)
        req = ApprovalRequest(approval_type=ApprovalType.AD_SPEND, title="Telegram budget setting change", entity_type="telegram_budget_policy", entity_id=policy.id, requested_by=actor, summary=json.dumps({"field": field, "old": str(old), "new": str(value)}))
        db.add(req)
        await db.flush()
        return f"Olivia: Proposed {field.replace('_', ' ')}: £{old} → £{value}. Local setting only; no advert launched. Confirm within 15 minutes: /confirm {req.id}\nCancel: /cancel {req.id}"
    try:
        ident = UUID(confirmation[2])
    except ValueError:
        return "Invalid confirmation reference."
    req = (await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == ident).with_for_update())).scalar_one_or_none()
    if not req or req.requested_by != actor or req.entity_type != "telegram_budget_policy" or req.status != ApprovalStatus.PENDING:
        return "No matching pending Telegram action."
    if confirmation[1] == "cancel" or datetime.now(UTC) - req.created_at > timedelta(minutes=15):
        req.status = ApprovalStatus.CANCELLED
        req.decided_at = datetime.now(UTC)
        return "Action cancelled or expired."
    data = json.loads(req.summary)
    field = data["field"]
    if field not in FIELDS.values():
        return "Unsupported setting."
    policy = (await db.execute(select(MarketingBudgetPolicy).where(MarketingBudgetPolicy.id == req.entity_id).with_for_update())).scalar_one_or_none()
    value = Decimal(data["new"])
    if not policy or getattr(policy, field) != Decimal(data["old"]) or not value.is_finite() or not 0 < value <= 100000:
        return "Setting changed since proposal or invalid value. Request a fresh proposal."
    setattr(policy, field, value)
    req.status = ApprovalStatus.APPROVED
    req.decided_at = datetime.now(UTC)
    await record_audit(db, actor_type="telegram_owner", actor_id=str(chat_id), action="marketing_budget_update", entity_type="marketing_budget_policy", entity_id=policy.id, detail=data)
    return f"Olivia: Saved {field.replace('_', ' ')} at £{value}. Dashboard updated; no external advertising action taken."
