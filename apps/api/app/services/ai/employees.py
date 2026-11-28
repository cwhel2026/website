"""Explicit specialist routing and least-privilege tool policies."""
import re

EMPLOYEES = {
    "personal_assistant": ("Alex", "You are Alex, the general SurfaceCoat assistant. Use saved pricing rules for job estimates and ask for missing inputs. Coordinate tasks and explain what can actually be done."),
    "marketing": ("Olivia", "You are Olivia, SurfaceCoat's marketing manager. Draft campaigns, content and growth recommendations. Never claim live research or advertising execution without evidence."),
    "finance": ("Arthur", "You are Arthur, SurfaceCoat's internal finance assistant. Distinguish recorded cash, estimated profit and reconciled accounts. Never authorise payments, tax filings or dividends."),
}
TOOLS = {
    "marketing": frozenset({"marketing_budget_policy", "new_enquiries", "analytics_snapshot", "marketing_capacity", "marketing_weekly_spend", "marketing_profitability", "marketing_integrations", "marketing_launch_readiness", "marketing_content_calendar"}),
    "finance": frozenset({"pricing_profile", "marketing_budget_policy", "analytics_snapshot", "marketing_weekly_spend", "finance_summary", "finance_tax_reserves", "finance_cashflow"}),
}
BLOCKED = {"marketing_pause_all", "marketing_director_proactive", "marketing_director_plan"}


def allowed_tool(agent_slug, name):
    return name not in BLOCKED and (agent_slug not in TOOLS or name in TOOLS[agent_slug])


def route_employee(text):
    match = re.match(r"^/?(alex|olivia|arthur|both)(?=$|[\s,:])\s*[:,]?\s*(.*)$", text.strip(), re.I | re.S)
    if not match:
        return (), text
    names = {"alex": ("personal_assistant",), "olivia": ("marketing",), "arthur": ("finance",), "both": ("marketing", "finance")}
    return names[match[1].lower()], match[2] or "Introduce yourself and explain what you can help with."
