from app.services.ai.campaign_forecast import forecast_campaign

def test_forecast():
    result = forecast_campaign(150, dict(cpm=10, frequency=2, ctr=.01, lead_rate=.05, quote_rate=.8, close_rate=.5, job_revenue=500, job_variable_cost=250))
    assert result["impressions"] == "15000.00"
    assert result["reach"] == "7500.00"
    assert result["jobs"] == "3.00"
    assert result["contribution_after_ads_gbp"] == "600.00"

def test_missing_assumptions():
    assert "error" in forecast_campaign(150, {})
