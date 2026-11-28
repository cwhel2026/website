from decimal import Decimal

from app.services.flexible_planning import discount_review


def test_discount_preserves_margin_without_assumed_savings():
    result = discount_review(Decimal("100"), Decimal("40"), Decimal("20"))
    assert result["illustrative_max_discount_ex_vat_gbp"] == "7.69"


def test_discount_zero_below_margin_floor():
    assert discount_review(100, 30, 20)["illustrative_max_discount_ex_vat_gbp"] == "0.00"


def test_discount_capped_at_recorded_travel():
    assert discount_review(100, 80, 5)["illustrative_max_discount_ex_vat_gbp"] == "5.00"
