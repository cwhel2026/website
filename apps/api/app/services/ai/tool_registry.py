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
    {
        "type": "function",
        "function": {
            "name": "marketing_integrations",
            "description": "Integration setup centre status for all marketing channels.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_director_proactive",
            "description": "Run proactive marketing director daily analysis with persistent recommendations.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_launch_readiness",
            "description": "Pre-launch checklist and external blockers.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "marketing_content_calendar",
            "description": "Scheduled and draft content for the next 7 days.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]


for name, description in [
    ("pricing_profile", "Active company pricing rules and provisional labour and material cost assumptions."),
    ("marketing_budget_policy", "Current saved marketing budget limits, not live spending."),
    ("finance_summary", "Recorded revenue and expense summary; provisional accounting basis."),
    ("finance_tax_reserves", "Tax reserve estimates and unknown liabilities."),
    ("finance_cashflow", "Provisional 30-day cash flow forecast."),
]:
    OPENAI_TOOL_SPECS.append({"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}})


async def run_tool(db: AsyncSession, name: str) -> dict[str, Any]:
    if name in {"marketing_pause_all", "marketing_director_proactive"}:
        return {"error": "Action requires explicit owner approval"}
    if name == "pricing_profile":
        from app.services.pricing_engine import get_active_pricing_profile, LABOUR_HOURS_PER_SQM, MATERIAL_COST_PER_SQM, DEFAULT_LABOUR_RATE
        profile = await get_active_pricing_profile(db)
        return {"version": profile.version, "rules": [{"type": r.rule_type.value, "surface": r.surface_type.value if r.surface_type else None, "category": r.service_category.value if r.service_category else None, "amount": str(r.amount_gbp), "percentage": str(r.percentage) if r.percentage is not None else None, "tier": r.label} for r in profile.rules if r.is_active], "labour_rate": str(DEFAULT_LABOUR_RATE), "labour_hours_per_sqm": {k.value: str(v) for k,v in LABOUR_HOURS_PER_SQM.items()}, "materials_per_sqm": {k.value: str(v) for k,v in MATERIAL_COST_PER_SQM.items()}, "basis": "Provisional engine assumptions, not verified Marl Coatings costs. Travel, VAT and surcharges require confirmation."}
    if name == "marketing_budget_policy":
        from app.models.marketing_ops import MarketingBudgetPolicy
        from app.services.marketing.budget_controls import _policy_dict
        from sqlalchemy import select
        policy = (await db.execute(select(MarketingBudgetPolicy).limit(1))).scalar_one_or_none()
        return _policy_dict(policy) if policy else {"error": "Budget policy not configured"}
    if name == "finance_summary":
        from app.services.analytics_service import revenue_and_expense_summary
        return await revenue_and_expense_summary(db)
    if name == "finance_tax_reserves":
        from app.services.finance.tax_reserves import compute_tax_reserves
        return await compute_tax_reserves(db)
    if name == "finance_cashflow":
        from app.services.finance.cashflow import simple_cashflow_forecast
        return await simple_cashflow_forecast(db)
    handler: ToolHandler | None = TOOL_HANDLERS.get(name)  # type: ignore[assignment]
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    return await handler(db)