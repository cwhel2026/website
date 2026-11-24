from decimal import Decimal

from app.services.materials_forecast import low_stock_alerts


class ScalarResult:
    def scalar_one_or_none(self):
        return None


class Item:
    def __init__(self, sku, qty, reorder):
        self.sku = sku
        self.name = sku
        self.quantity_on_hand = qty
        self.reorder_level = reorder


class Scalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class Exec:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return Scalars(self._items)


class FakeSession:
    async def execute(self, stmt):
        return Exec([Item("COAT", Decimal("5"), Decimal("15")), Item("CHEM", Decimal("10"), Decimal("4"))])


async def _run():
    return await low_stock_alerts(FakeSession())


def test_low_stock_detected():
    alerts = __import__("asyncio").run(_run())
    assert len(alerts) == 1
    assert alerts[0]["sku"] == "COAT"