"""Inbound webhooks fail closed; none of these requests reach the database."""

import hashlib
import hmac
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.routers import marketing_webhooks

BODY = b'{"object":"page","entry":[]}'


def _client(monkeypatch, **settings) -> TestClient:
    defaults = {"meta_app_secret": None, "meta_webhook_verify_token": None, "email_inbound_webhook_secret": None}
    defaults.update(settings)
    monkeypatch.setattr(marketing_webhooks, "get_settings", lambda: SimpleNamespace(**defaults))
    app = FastAPI()
    app.include_router(marketing_webhooks.router)
    return TestClient(app)


@pytest.mark.parametrize("path", ["/marketing/webhooks/meta/leads", "/marketing/webhooks/meta/feed"])
def test_meta_post_refused_without_app_secret(monkeypatch, path):
    assert _client(monkeypatch).post(path, content=BODY).status_code == 503


@pytest.mark.parametrize(
    "header",
    [None, "", "sha1=abc", "sha256=", "sha256=" + "0" * 64, "garbage"],
)
def test_meta_post_refused_with_bad_signature(monkeypatch, header):
    client = _client(monkeypatch, meta_app_secret="s3cret")
    headers = {"X-Hub-Signature-256": header} if header is not None else {}
    assert client.post("/marketing/webhooks/meta/leads", content=BODY, headers=headers).status_code == 403


def test_meta_signature_over_different_body_refused(monkeypatch):
    client = _client(monkeypatch, meta_app_secret="s3cret")
    sig = "sha256=" + hmac.new(b"s3cret", b"other", hashlib.sha256).hexdigest()
    res = client.post("/marketing/webhooks/meta/leads", content=BODY, headers={"X-Hub-Signature-256": sig})
    assert res.status_code == 403


def test_meta_subscription_challenge_uses_dotted_params(monkeypatch):
    client = _client(monkeypatch, meta_webhook_verify_token="verify-me")
    ok = client.get(
        "/marketing/webhooks/meta/leads",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "1234"},
    )
    assert ok.status_code == 200 and ok.json() == 1234
    bad = client.get(
        "/marketing/webhooks/meta/leads",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1234"},
    )
    assert bad.status_code == 403


def test_meta_subscription_refused_when_token_unset(monkeypatch):
    res = _client(monkeypatch).get(
        "/marketing/webhooks/meta/feed", params={"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "1"}
    )
    assert res.status_code == 503


def test_email_inbound_requires_shared_secret(monkeypatch):
    unset = _client(monkeypatch)
    assert unset.post("/marketing/webhooks/email/inbound", json={"from": "a@b.c"}).status_code == 503
    client = _client(monkeypatch, email_inbound_webhook_secret="x" * 32)
    assert client.post("/marketing/webhooks/email/inbound", json={"from": "a@b.c"}).status_code == 403
    res = client.post(
        "/marketing/webhooks/email/inbound", json={"from": "a@b.c"}, headers={"X-Webhook-Secret": "y" * 32}
    )
    assert res.status_code == 403
