from decimal import Decimal as D
import pytest
from app.services.material_costing import estimate_coating


def test_coating_consumption_and_pack_rounding():
    result = estimate_coating(area=D("60"), coverage=D("4"), coats=2, pack_litres=D("20"), pack_cost=D("100"), waste_percent=D("10"), revenue=D("600"), other_costs=D("75"))
    assert result["litres_required"] == D("33")
    assert result["packs_required"] == 2
    assert result["purchase_cost_gbp"] == D("200")
    assert result["estimated_contribution_gbp"] == D("360")


def test_zero_coverage_rejected():
    with pytest.raises(ValueError):
        estimate_coating(area=D("60"), coverage=D("0"), coats=2, pack_litres=D("20"), pack_cost=D("100"), waste_percent=D("10"), revenue=D("600"), other_costs=D("75"))
