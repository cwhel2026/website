"""Editable four-week £600 launch programme — Preston Meta focus."""

from __future__ import annotations

from decimal import Decimal


DEFAULT_LAUNCH_PROGRAMME = {
    "objective": "lead_generation",
    "platforms": ["facebook", "instagram"],
    "weekly_budget_gbp": 150,
    "total_weeks": 4,
    "total_budget_gbp": 600,
    "geo": {
        "centre": "Preston, Lancashire",
        "radius_miles": 20,
        "note": "Broad local adults — refine when data allows",
    },
    "structure": {
        "campaigns_max": 1,
        "ad_sets_max": 1,
        "initial_creatives": 3,
        "cta": "Get a free quote",
        "placements": "advantage_plus",
    },
    "weeks": [
        {
            "week": 1,
            "budget_gbp": 150,
            "goal": "Test three creatives; baseline CPM, CPC, CPL",
        },
        {
            "week": 2,
            "budget_gbp": 150,
            "goal": "Review lead quality and creative effectiveness",
        },
        {
            "week": 3,
            "budget_gbp": 150,
            "goal": "Improve enquiry conversion, targeting, messaging",
        },
        {
            "week": 4,
            "budget_gbp": 150,
            "goal": "Assess CAC, job profitability, scaling hypothesis",
        },
    ],
    "hypothesis_weekly_enquiries": "10–20 is a planning target, not guaranteed",
    "operational_launch": "2027-03-01",
}


async def ensure_launch_programme(policy) -> dict:
    if policy.launch_programme_json:
        return policy.launch_programme_json
    policy.launch_programme_json = DEFAULT_LAUNCH_PROGRAMME
    if not policy.geo_target_json:
        policy.geo_target_json = DEFAULT_LAUNCH_PROGRAMME["geo"]
    if policy.meta_weekly_budget_gbp <= 0:
        policy.meta_weekly_budget_gbp = Decimal("150")
    if policy.weekly_limit_gbp <= 0:
        policy.weekly_limit_gbp = Decimal("150")
    return policy.launch_programme_json