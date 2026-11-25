"""Authorised assistant tools exposed to language-model providers."""

from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assistant_tools import TOOL_HANDLERS

ToolHandler = Callable[[AsyncSession], Awaitable[dict[str, Any]]]

OPENAI_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "jobs_today",
            "description": "List today's appointments in Europe/London timezone.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "jobs_tomorrow",
            "description": "List tomorrow's appointments (UK calendar).",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "jobs_next_week",
            "description": "Appointment counts for the next 7 days from today (UK).",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pending_approvals",
            "description": "Pending approval queue items.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wash_pending_coat",
            "description": "Jobs washed but awaiting coating.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "quotations_awaiting",
            "description": "Quotations requiring owner approval.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rain_risk_coating",
            "description": "Coating appointments flagged unsuitable by last weather check.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "new_enquiries",
            "description": "Count of new enquiries in the last 7 days.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analytics_snapshot",
            "description": "30-day funnel and revenue snapshot from database records.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_capacity",
            "description": "Global spare capacity and territory advertising recommendations.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_weekly_spend",
            "description": "Recorded advertising spend in the last 7 days by platform.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_director_plan",
            "description": "Daily marketing director plan with budget policy, capacity and priority actions.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_profitability",
            "description": "30-day provisional marketing funnel and ROAS metrics.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]


async def run_tool(db: AsyncSession, name: str) -> dict[str, Any]:
    handler: ToolHandler | None = TOOL_HANDLERS.get(name)  # type: ignore[assignment]
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    return await handler(db)