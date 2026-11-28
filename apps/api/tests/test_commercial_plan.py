from app.services.ai.commercial_plan import plan_campaign

def test_hypothetical_budget():
    capacity = {"recommend_advertising": True, "territories": [{"territory_name": "Preston", "allocated_spare_slots": 3, "demand_score": 2}]}
    policy = {"weekly_limit_gbp": 150, "daily_limit_gbp": 22, "monthly_limit_gbp": 600, "live_paid_spend_approved": False}
    result = plan_campaign(capacity, policy, {"total_spent_gbp": 0}, 150)
    assert result["allocation"][0]["total_gbp"] == "149.94"
    assert result["authorised_spend_gbp"] == "0"

def test_missing_budget():
    assert "error" in plan_campaign({}, {}, {}, 150)
