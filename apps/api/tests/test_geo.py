from decimal import Decimal

from app.services.geo import estimate_drive_minutes, haversine_km


def test_haversine_burscough_to_preston_approx():
    # Burscough to Preston city centre ~15-20 km
    d = haversine_km(53.5977, -2.8407, 53.7632, -2.7031)
    assert Decimal("10") < d < Decimal("30")


def test_drive_minutes_positive():
    assert estimate_drive_minutes(Decimal("30")) >= 1