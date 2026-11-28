from decimal import Decimal
from app.services.ai.task_commands import parse_task
from app.services.ai.tool_registry import coating_estimate


def test_task_parser():
    assert parse_task("assign to Olivia: Review Preston leads") == ("marketing", "Review Preston leads")
    assert parse_task("/task Arthur review costs") == ("finance", "review costs")
    assert parse_task("/task unknown review costs") is None
    assert parse_task("/task Alex " + "x" * 241) is None


def test_costing():
    args = dict(area=100, coverage=5, coats=2, pack_litres=20, pack_cost=100, waste_percent=0, revenue=1000, other_costs=300)
    result = coating_estimate(args)
    assert result["packs_required"] == 2
    assert result["estimated_contribution_gbp"] == 500
    assert result["margin_percent"] == Decimal("50")
    assert result["markup_percent"] == Decimal("100")
    assert "error" in coating_estimate(dict(args, coats=1.5))
    assert "error" in coating_estimate(dict(args, coverage=0))
