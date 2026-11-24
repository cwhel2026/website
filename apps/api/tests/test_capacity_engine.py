from decimal import Decimal

from app.services.marketing.capacity_engine import GlobalCapacitySnapshot


def test_global_capacity_recommends_pause_when_full():
    snap = GlobalCapacitySnapshot(
        horizon_days=14,
        max_slots=10,
        booked_slots=10,
        spare_slots=0,
        spare_score=0,
        max_appointments_per_day=2,
        recommend_advertising=False,
        advertising_daily_budget_cap_gbp=Decimal("0"),
        note="Diary at or above practical capacity — do not increase paid demand.",
    )
    assert snap.recommend_advertising is False
    assert snap.spare_slots == 0