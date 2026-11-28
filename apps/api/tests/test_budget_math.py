from app.services.ai.budget_math import validate_allocation

def test_actual_telegram_overspend():
    rows = [{"territory": name, "daily_gbp": "11.67", "days": 7} for name in ("West Lancashire", "Preston", "Manchester")]
    result = validate_allocation(150, 0, rows)
    assert not result["valid"]
    assert result["total_gbp"] == "245.07"
    assert result["overspend_gbp"] == "95.07"

def test_remaining_budget():
    assert validate_allocation(150, 80, [{"territory": "Preston", "daily_gbp": 10, "days": 7}])["valid"]
    assert not validate_allocation(150, 81, [{"territory": "Preston", "daily_gbp": 10, "days": 7}])["valid"]

def test_invalid():
    assert not validate_allocation(150, 0, [{"territory": "Preston", "daily_gbp": "NaN", "days": 7}])["valid"]
