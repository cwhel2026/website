from decimal import Decimal

from app.services.finance.bookkeeping.categorizer import suggest_for_description
from app.models.finance import ExpenseCategory


def test_fuel_categorisation():
    s = suggest_for_description("SHELL FUEL STATION", Decimal("-54.20"))
    assert s.category == ExpenseCategory.FUEL
    assert s.confidence >= 80
    assert s.receipt_required is True


def test_income_low_confidence():
    s = suggest_for_description("CUSTOMER PAYMENT SMITH", Decimal("420.00"))
    assert s.confidence < 60


def test_materials_merchant():
    s = suggest_for_description("SCREWFIX 1234", Decimal("-89.99"))
    assert s.category == ExpenseCategory.MATERIALS