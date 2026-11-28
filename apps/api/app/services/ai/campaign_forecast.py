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
        quotes = enquiries * quote
        jobs = quotes * close
        def fmt(x):
            return str(x.quantize(Decimal(".01")))
        return {"basis": "Scenario assumptions, not verified platform estimates", "impressions": fmt(impressions), "reach": fmt(impressions/frequency), "clicks": fmt(clicks), "enquiries": fmt(enquiries), "quotes": fmt(quotes), "jobs": fmt(jobs), "cpc_gbp": fmt(b/clicks) if clicks else None, "cac_gbp": fmt(b/jobs) if jobs else None, "revenue_gbp": fmt(jobs*revenue), "contribution_after_ads_gbp": fmt(jobs*(revenue-cost)-b)}
    except (KeyError, TypeError, ValueError, InvalidOperation, ArithmeticError):
        return {"error": "Valid forecast assumptions required"}
