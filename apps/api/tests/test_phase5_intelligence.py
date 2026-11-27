from types import SimpleNamespace

from app.services.business_director import task_identity
from app.routers import telegram


def test_director_dedupes_count_changes_but_not_stock_skus():
    def task(action, payload):
        return SimpleNamespace(agent_slug="inventory", action_key=action, payload_json=payload)
    assert task_identity(task("review", '{"count":1}')) == task_identity(task("review", '{"count":2}'))
    assert task_identity(task("replenish_stock", '{"sku":"A"}')) != task_identity(task("replenish_stock", '{"sku":"B"}'))


def test_telegram_requires_admin_private_chat(monkeypatch):
    monkeypatch.setattr(telegram, "get_settings", lambda: SimpleNamespace(telegram_admin_id_list=[123], telegram_owner_chat_id=123))
    assert telegram._authorised_chat(123, 123)
    assert not telegram._authorised_chat(-100, 123)
    assert not telegram._authorised_chat(123, 456)
    assert not telegram._authorised_chat(123, None)
