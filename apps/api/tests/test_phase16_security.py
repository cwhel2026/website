from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.notifications.outbox import telegram_recipients


def test_private_reply_never_broadcasts_even_with_legacy_category():
    settings = SimpleNamespace(telegram_admin_id_list=[1, 2], telegram_alert_chat_ids=[1, 2, -100])
    assert telegram_recipients("integration_failure", {"reply_chat_id": 2}, settings) == [2]
    assert telegram_recipients("integration_failure", {"reply_chat_id": 3}, settings) == []
    assert telegram_recipients("quotation", {}, settings) == [1, 2]


def test_api_response_is_not_cacheable():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    @app.get("/api/v1/private")
    def private():
        return {"ok": True}
    response = TestClient(app).get("/api/v1/private")
    assert response.headers["cache-control"] == "no-store, private"
