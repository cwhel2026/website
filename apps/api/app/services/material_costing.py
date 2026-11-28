"""Explicit-input coating estimates; no assumed manufacturer coverage."""
from decimal import Decimal, ROUND_CEILING


def estimate_coating(*, area: Decimal, coverage: Decimal, coats: int, pack_litres: Decimal, pack_cost: Decimal, waste_percent: Decimal, revenue: Decimal, other_costs: Decimal) -> dict:
    values = (area, coverage, pack_litres, pack_cost, waste_percent, revenue, other_costs)
    if any(not x.is_finite() for x in values):
        raise ValueError("Finite inputs required")
    if min(area, coverage, pack_litres) <= 0 or min(pack_cost, revenue, other_costs, waste_percent) < 0 or not 1 <= coats <= 10 or waste_percent > 100:
        raise ValueError("Invalid coating estimate inputs")
    litres = area * coats / coverage * (1 + waste_percent / 100)
    packs = (litres / pack_litres).to_integral_value(rounding=ROUND_CEILING)
    consumed_cost = litres * pack_cost / pack_litres
    return {"litres_required": litres, "packs_required": packs, "purchase_cost_gbp": packs * pack_cost, "estimated_consumed_cost_gbp": consumed_cost, "estimated_contribution_gbp": revenue - consumed_cost - other_costs, "basis": "owner supplied inputs; excludes unlisted costs and tax"}
