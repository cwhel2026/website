"""Liveness evidence for the worker and the beat scheduler, stored in the database.

* ``worker`` row: written when a worker process becomes ready.
* ``beat`` row: written every minute by ``rmd.scheduler_heartbeat``. Because the
  task is scheduled by beat and executed by a worker, a fresh row proves the
  broker, beat and at least one worker are all working end to end.
"""

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime

from celery.signals import worker_ready
from sqlalchemy import text

from app.database_sync import SessionLocal
from app.worker.celery_app import celery_app

_UPSERT = text(
    "INSERT INTO scheduler_heartbeats (component, hostname, last_beat_at, detail_json) "
    "VALUES (:c, :h, :t, :d) "
    "ON CONFLICT (component) DO UPDATE SET hostname = EXCLUDED.hostname, "
    "last_beat_at = EXCLUDED.last_beat_at, detail_json = EXCLUDED.detail_json"
)


def record_heartbeat(component: str, detail: dict | None = None) -> datetime:
    now = datetime.now(UTC)
    with SessionLocal() as session:
        session.execute(
            _UPSERT,
            {"c": component, "h": socket.gethostname(), "t": now, "d": json.dumps(detail or {})},
        )
        session.commit()
    return now


@celery_app.task(name="rmd.scheduler_heartbeat", bind=True, guarded=False, max_retries=0)
def scheduler_heartbeat(self) -> dict:
    at = record_heartbeat("beat", {"task_id": self.request.id})
    return {"ok": True, "at": at.isoformat()}


@worker_ready.connect
def _on_worker_ready(sender=None, **_):
    record_heartbeat("worker", {"event": "worker_ready"})
