"""GuardedTask behaviour against a real Redis (set REDIS_TEST_URL)."""

import os
import uuid

import pytest

REDIS_URL = os.getenv("REDIS_TEST_URL", "")
pytestmark = pytest.mark.skipif(not REDIS_URL, reason="REDIS_TEST_URL not set")


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("REDIS_URL", REDIS_URL)
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    from app.config import get_settings
    from app.worker import guard

    get_settings.cache_clear()
    guard.redis_client.cache_clear()
    from celery import Celery

    test_app = Celery("guard-test", broker="memory://", task_cls="app.worker.guard:GuardedTask")
    test_app.conf.task_always_eager = True
    test_app.conf.task_eager_propagates = False
    yield test_app
    guard.redis_client.cache_clear()
    get_settings.cache_clear()


def test_transient_errors_retry_then_succeed(app):
    calls = {"n": 0}
    name = f"test.flaky.{uuid.uuid4().hex}"

    @app.task(name=name, bind=True, retry_backoff=False, retry_jitter=False)
    def flaky(self):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("broker blip")
        return "ok"

    assert flaky.apply().get() == "ok"
    assert calls["n"] == 3


def test_non_transient_errors_do_not_retry(app):
    calls = {"n": 0}
    name = f"test.broken.{uuid.uuid4().hex}"

    @app.task(name=name, bind=True)
    def broken(self):
        calls["n"] += 1
        raise ValueError("bug")

    result = broken.apply()
    assert result.failed()
    assert calls["n"] == 1


def test_duplicate_slot_and_overlap_are_skipped(app):
    from app.worker.guard import lock_key, redis_client

    name = f"test.once.{uuid.uuid4().hex}"
    runs = {"n": 0}

    @app.task(name=name, bind=True)
    def once(self):
        runs["n"] += 1
        return "ran"

    assert once.apply().get() == "ran"
    assert once.apply().get() == {"skipped": "duplicate_slot"}
    assert runs["n"] == 1

    other = f"test.overlap.{uuid.uuid4().hex}"

    @app.task(name=other, bind=True)
    def overlapping(self):
        return "ran"

    redis_client().set(lock_key(other), "held-by-another-run", ex=30)
    assert overlapping.apply().get() == {"skipped": "already_running"}
