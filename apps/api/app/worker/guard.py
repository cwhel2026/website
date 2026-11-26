"""Base Celery task: bounded retries, duplicate-slot and overlap protection.

* Retries: only transient infrastructure errors (database connection, network),
  at most 2 retries with exponential backoff and jitter.
* Duplicate scheduled runs: the first attempt of a task claims a per-minute slot
  in Redis (SET NX). A second beat process, or a re-delivered message for the
  same minute, finds the slot taken and exits without running.
* Overlap: a per-task Redis lock (SET NX with expiry above the hard time limit)
  prevents two executions of the same task at once.

If Redis is unreachable the task does not run at all; Redis is also the broker,
so a missing Redis already means no tasks are delivered.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from functools import lru_cache

import httpx
import redis
from celery import Task
from sqlalchemy.exc import InterfaceError, OperationalError

from app.config import get_settings

logger = logging.getLogger("rmd.worker")

TRANSIENT_ERRORS = (
    OperationalError,
    InterfaceError,
    ConnectionError,
    TimeoutError,
    httpx.TransportError,
)

_RELEASE_LUA = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


@lru_cache(maxsize=1)
def redis_client() -> redis.Redis:
    settings = get_settings()
    url = settings.celery_broker_url or settings.redis_url
    return redis.Redis.from_url(url, socket_timeout=3, socket_connect_timeout=3)


def slot_key(task_name: str, when: datetime | None = None) -> str:
    when = when or datetime.now(UTC)
    return f"rmd:slot:{task_name}:{when:%Y%m%d%H%M}"


def lock_key(task_name: str) -> str:
    return f"rmd:lock:{task_name}"


class GuardedTask(Task):
    autoretry_for = TRANSIENT_ERRORS
    max_retries = 2
    retry_backoff = 30
    retry_backoff_max = 600
    retry_jitter = True
    guarded = True

    def __call__(self, *args, **kwargs):
        if not self.guarded or self.request.called_directly:
            return super().__call__(*args, **kwargs)

        client = redis_client()
        if (self.request.retries or 0) == 0:
            if not client.set(slot_key(self.name), self.request.id or "1", nx=True, ex=3600):
                logger.warning("task %s skipped: duplicate run for this minute", self.name)
                return {"skipped": "duplicate_slot"}

        token = uuid.uuid4().hex
        hard_limit = self.time_limit or self.app.conf.task_time_limit or 360
        key = lock_key(self.name)
        if not client.set(key, token, nx=True, ex=int(hard_limit) + 60):
            logger.warning("task %s skipped: previous run still in progress", self.name)
            return {"skipped": "already_running"}
        try:
            # Not super().__call__: that pushes a fresh request and hides the worker's
            # (task id, retries), which turns autoretry into a plain failure.
            return self.run(*args, **kwargs)
        finally:
            try:
                client.eval(_RELEASE_LUA, 1, key, token)
            except redis.RedisError:
                logger.exception("task %s: lock release failed (expires automatically)", self.name)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "task %s failed permanently after %s retries: %s",
            self.name,
            self.request.retries,
            exc,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
