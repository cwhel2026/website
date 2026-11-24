import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assistant_tools import TOOL_HANDLERS


INTENT_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"\btomorrow\b", re.I), ["jobs_tomorrow"]),
    (re.compile(r"\bnext week\b", re.I), ["jobs_next_week"]),
    (re.compile(r"paint|coat", re.I), ["wash_pending_coat"]),
    (re.compile(r"\bapproval", re.I), ["pending_approvals", "quotations_awaiting"]),
    (re.compile(r"\brain\b", re.I), ["rain_risk_coating"]),
    (re.compile(r"\benquir", re.I), ["new_enquiries"]),
    (re.compile(r"\btoday\b", re.I), ["jobs_tomorrow", "pending_approvals"]),
]


async def answer_question(db: AsyncSession, question: str) -> tuple[str, dict[str, Any]]:
    """Deterministic assistant — uses backend tools only, no fabricated data."""
    tools_to_run: list[str] = []
    for pattern, tools in INTENT_PATTERNS:
        if pattern.search(question):
            tools_to_run.extend(tools)
    if not tools_to_run:
        tools_to_run = ["jobs_tomorrow", "pending_approvals", "wash_pending_coat"]

    # dedupe preserve order
    seen: set[str] = set()
    unique = [t for t in tools_to_run if not (t in seen or seen.add(t))]

    tool_data: dict[str, Any] = {}
    for name in unique:
        handler = TOOL_HANDLERS.get(name)
        if handler:
            tool_data[name] = await handler(db)

    parts: list[str] = []
    if "jobs_tomorrow" in tool_data:
        d = tool_data["jobs_tomorrow"]
        parts.append(
            f"Tomorrow ({d['date']}) you have {d['count']} appointment(s)."
        )
        for a in d["appointments"][:5]:
            parts.append(f"• {a['job_reference']} — {a['type']} at {a['start']}")

    if "jobs_next_week" in tool_data:
        d = tool_data["jobs_next_week"]
        parts.append(f"Next 7 days: {d['total']} scheduled appointment(s) across {len(d['days'])} day(s).")

    if "wash_pending_coat" in tool_data:
        d = tool_data["wash_pending_coat"]
        parts.append(f"Driveways awaiting coating: {d['count']}.")
        for j in d["jobs"][:5]:
            parts.append(f"• {j['reference']} (target {j['target_date'] or 'TBC'})")

    if "pending_approvals" in tool_data:
        d = tool_data["pending_approvals"]
        parts.append(f"Approval centre: {d['count']} pending item(s).")

    if "rain_risk_coating" in tool_data:
        d = tool_data["rain_risk_coating"]
        parts.append(f"Coating appointments flagged unsuitable by last weather check: {d['count']}.")

    if "new_enquiries" in tool_data:
        parts.append(
            f"New enquiries in the last 7 days: {tool_data['new_enquiries']['last_7_days_new_enquiries']}."
        )

    if not parts:
        return "I could not find matching business data for that question.", tool_data

    return "\n".join(parts), tool_data