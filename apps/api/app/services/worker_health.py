"""Worker / scheduler health derived from recorded evidence only.

Nothing here infers that a task works: a schedule entry is reported as
operational only when a successful run has actually been recorded.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJobRun, JobRunStatus, SchedulerHeartbeat

HEARTBEAT_STALE_AFTER = timedelta(minutes=3)


def _schedule_entries() -> list[dict]:
    from app.worker.celery_app import celery_app

    out = []
    now = datetime.now(UTC)
    for key, entry in celery_app.conf.beat_schedule.items():
        sched = entry["schedule"]
        sched.app = celery_app
        try:
            remaining = sched.remaining_estimate(sched.maybe_make_aware(sched.now()))
            next_run = (now + remaining + timedelta(seconds=30)).replace(second=0, microsecond=0)
        except Exception:
            next_run = None
        out.append(
            {
                "key": key,
                "task": entry["task"],
                "task_name": entry["task"].removeprefix("rmd."),
                "schedule": str(sched),
                "next_run_at": next_run.isoformat() if next_run else None,
            }
        )
    return out


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


async def worker_health(db: AsyncSession, *, broker_ping: bool | None) -> dict:
    now = datetime.now(UTC)
    beats = {
        hb.component: hb for hb in (await db.execute(select(SchedulerHeartbeat))).scalars().all()
    }
    beat = beats.get("beat")
    worker = beats.get("worker")
    beat_age = (now - beat.last_beat_at).total_seconds() if beat else None
    scheduler_live = beat is not None and (now - beat.last_beat_at) <= HEARTBEAT_STALE_AFTER

    entries = _schedule_entries()
    names = [e["task_name"] for e in entries if e["task_name"] != "scheduler_heartbeat"]

    async def _last(name: str, status: JobRunStatus) -> BackgroundJobRun | None:
        return (
            await db.execute(
                select(BackgroundJobRun)
                .where(BackgroundJobRun.task_name == name, BackgroundJobRun.status == status)
                .order_by(desc(BackgroundJobRun.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()

    since = now - timedelta(hours=24)
    counts = {
        (row[0], row[1]): row[2]
        for row in (
            await db.execute(
                select(BackgroundJobRun.task_name, BackgroundJobRun.status, func.count())
                .where(BackgroundJobRun.created_at >= since)
                .group_by(BackgroundJobRun.task_name, BackgroundJobRun.status)
            )
        ).all()
    }

    schedules = []
    for e in entries:
        if e["task_name"] == "scheduler_heartbeat":
            e.update(
                {
                    "last_success_at": _iso(beat.last_beat_at) if beat else None,
                    "last_failure_at": None,
                    "last_error": None,
                    "status": "ok" if scheduler_live else ("stale" if beat else "never_run"),
                    "runs_24h": None,
                    "failures_24h": None,
                }
            )
            schedules.append(e)
            continue
        ok = await _last(e["task_name"], JobRunStatus.SUCCEEDED)
        bad = await _last(e["task_name"], JobRunStatus.FAILED)
        if ok is None and bad is None:
            status = "never_run"
        elif bad is not None and (ok is None or bad.created_at > ok.created_at):
            status = "failing"
        else:
            status = "ok"
        e.update(
            {
                "last_success_at": _iso(ok.finished_at or ok.created_at) if ok else None,
                "last_failure_at": _iso(bad.finished_at or bad.created_at) if bad else None,
                "last_error": (bad.error_message or "")[:300] if bad else None,
                "status": status,
                "runs_24h": sum(v for (n, _), v in counts.items() if n == e["task_name"]),
                "failures_24h": counts.get((e["task_name"], JobRunStatus.FAILED), 0),
            }
        )
        schedules.append(e)

    failures = (
        await db.execute(
            select(BackgroundJobRun)
            .where(BackgroundJobRun.status == JobRunStatus.FAILED)
            .order_by(desc(BackgroundJobRun.created_at))
            .limit(20)
        )
    ).scalars().all()

    unverified = [s["task_name"] for s in schedules if s["status"] == "never_run" and s["task_name"] in names]
    if broker_ping is False:
        overall = "broker_unreachable"
    elif beat is None:
        overall = "no_worker_evidence"
    elif not scheduler_live:
        overall = "scheduler_stale"
    elif any(s["status"] == "failing" for s in schedules):
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "overall": overall,
        "checked_at": now.isoformat(),
        "broker_reachable": broker_ping,
        "scheduler": {
            "live": scheduler_live,
            "last_heartbeat_at": _iso(beat.last_beat_at) if beat else None,
            "heartbeat_age_seconds": round(beat_age) if beat_age is not None else None,
            "hostname": beat.hostname if beat else None,
        },
        "worker": {
            "last_ready_at": _iso(worker.last_beat_at) if worker else None,
            "hostname": worker.hostname if worker else None,
        },
        "schedules": schedules,
        "never_run": unverified,
        "recent_failures": [
            {
                "task_name": f.task_name,
                "at": _iso(f.finished_at or f.created_at),
                "error": (f.error_message or "")[:300],
                "detail": json.loads(f.detail_json or "{}") if f.detail_json else {},
            }
            for f in failures
        ],
    }
