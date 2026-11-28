from decimal import Decimal
from app.services.ai.owner_actions import parse_budget


def test_budget_command():
    assert parse_budget("Olivia, change our facebook weekly budget to £100") == ("meta_weekly_budget_gbp", Decimal("100"))
    assert parse_budget("set marketing weekly budget to 150.25") == ("weekly_limit_gbp", Decimal("150.25"))


def test_invalid_budget_command():
    for text in ("set marketing weekly budget to 0", "set marketing weekly budget to -1", "set marketing weekly budget to NaN", "set marketing weekly budget to 100001", "set live paid spend to true"):
        assert parse_budget(text) is None
