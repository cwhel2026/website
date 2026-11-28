from decimal import Decimal, InvalidOperation, ROUND_DOWN

def plan_campaign(capacity, policy, spend, requested):
    try:
        values = [Decimal(str(v)) for v in (requested, policy["weekly_limit_gbp"], policy["daily_limit_gbp"], policy["monthly_limit_gbp"], spend["total_spent_gbp"])]
        if any(not v.is_finite() or v < 0 for v in values):
            raise ValueError()
        requested, weekly, daily, monthly, spent = values
        cap = max(Decimal(0), min(requested, weekly - spent, daily * 7, monthly))
        per_day = (cap / 7).quantize(Decimal(".01"), rounding=ROUND_DOWN)
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return {"error": "Budget evidence unavailable", "authorised_spend_gbp": "0"}
    candidates = [t for t in capacity.get("territories", []) if t.get("allocated_spare_slots", 0) >= 2 and t.get("territory_name")]
    candidates.sort(key=lambda t: (-t.get("demand_score", 0), t.get("appointments_next_14_days", 0), t["territory_name"]))
    result = {"authorised_spend_gbp": "0", "hypothetical": True, "recorded_spend_provisional": True,
              "free_actions": ["Prepare before-and-after creative using authorised photos", "Review existing quotation follow-ups for owner approval", "Research local commercial properties using verified public listings"],
              "launch_blockers": ["Verify bank affordability, platform billing, channel limits and owner approval"],
              "allocation": []}
    if not candidates or not capacity.get("recommend_advertising") or per_day <= 0:
        result["reason"] = "No eligible capacity or remaining budget in recorded evidence"
        return result
    t = candidates[0]
    result.update({"allocation": [{"territory": t["territory_name"], "daily_gbp": str(per_day), "days": 7, "total_gbp": str(per_day * 7)}],
                   "evidence": {"demand_score": t.get("demand_score", 0), "allocated_spare_slots": t["allocated_spare_slots"]},
                   "reason": "Highest recorded demand score among eligible territories; ties use fewer appointments then alphabetical order. Zero demand score is a test hypothesis, not proven demand.",
                   "measurement": "Track qualified enquiries, accepted quotes and collected revenue linked to campaign; review after seven days before increasing spend.",
                   "stop_rule": "Stop on budget cap, unsuitable capacity, or missing attribution; no automatic spend."})
    return result


def scenario_reach(budget):
    """Explicit sensitivity inputs, not market benchmarks or platform estimates."""
    from .campaign_forecast import forecast_campaign
    scenarios = {}
    for name, cpm, frequency, ctr, lead, quote, close in (
        ("conservative", 20, 3, .005, .02, .5, .2),
        ("illustrative_mid", 10, 2, .01, .05, .8, .5),
        ("optimistic", 5, 1.5, .015, .08, .8, .6),
    ):
        assumptions = dict(cpm=cpm, frequency=frequency, ctr=ctr, lead_rate=lead, quote_rate=quote, close_rate=close, job_revenue=0, job_variable_cost=0)
        forecast = forecast_campaign(budget, assumptions)
        for key in ("revenue_gbp", "contribution_after_ads_gbp"):
            forecast.pop(key, None)
        assumptions.pop("job_revenue")
        assumptions.pop("job_variable_cost")
        scenarios[name] = {"assumptions": assumptions, "forecast": forecast}
    return scenarios
