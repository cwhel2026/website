from decimal import Decimal, InvalidOperation

def forecast_campaign(budget, assumptions):
    """Scenario estimates, never platform forecasts or guaranteed outcomes."""
    try:
        b = Decimal(str(budget))
        keys = ("cpm", "frequency", "ctr", "lead_rate", "quote_rate", "close_rate", "job_revenue", "job_variable_cost")
        cpm, frequency, ctr, lead, quote, close, revenue, cost = [Decimal(str(assumptions[k])) for k in keys]
        if any(not x.is_finite() or x < 0 for x in (b,cpm,frequency,ctr,lead,quote,close,revenue,cost)) or cpm <= 0 or frequency < 1 or any(x > 1 for x in (ctr,lead,quote,close)):
            raise ValueError()
        impressions = b / cpm * 1000
        clicks = impressions * ctr
        enquiries = clicks * lead
        qualified_rate = Decimal(str(assumptions.get("qualified_rate", 1)))
        capacity = Decimal(str(assumptions.get("capacity_jobs", "1000000000")))
        if not qualified_rate.is_finite() or not 0 <= qualified_rate <= 1 or not capacity.is_finite() or capacity < 0:
            raise ValueError()
        qualified = enquiries * qualified_rate
        quotes = qualified * quote
        jobs = quotes * close
        fulfilled = min(jobs, capacity)
        def fmt(x):
            return str(x.quantize(Decimal(".01")))
        return {"basis": "Scenario assumptions, not verified platform estimates", "impressions": fmt(impressions), "reach": fmt(impressions/frequency), "clicks": fmt(clicks), "enquiries": fmt(enquiries), "quotes": fmt(quotes), "jobs": fmt(jobs), "qualified_leads": fmt(qualified), "fulfillable_jobs": fmt(fulfilled), "unfulfilled_demand": fmt(max(Decimal(0), jobs-capacity)), "break_even_cac_gbp": fmt(max(Decimal(0), revenue-cost)), "break_even_jobs": fmt(b/(revenue-cost)) if revenue > cost else None, "ctr": str(ctr), "cpm_gbp": str(cpm), "frequency": str(frequency), "cpc_gbp": fmt(b/clicks) if clicks else None, "cac_gbp": fmt(b/fulfilled) if fulfilled else None, "revenue_gbp": fmt(fulfilled*revenue), "contribution_after_ads_gbp": fmt(fulfilled*(revenue-cost)-b)}
    except (KeyError, TypeError, ValueError, InvalidOperation, ArithmeticError):
        return {"error": "Valid forecast assumptions required"}
