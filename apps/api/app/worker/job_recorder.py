import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.background_job import BackgroundJobRun, JobRunStatus


def start_run(session: Session, task_name: str, dedupe_key: str | None, worker_id: str | None) -> BackgroundJobRun:
    run = BackgroundJobRun(
        id=uuid4(),
        task_name=task_name,
        dedupe_key=dedupe_key,
        status=JobRunStatus.RUNNING,
        worker_id=worker_id,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    return run


def finish_run(
    session: Session,
    run: BackgroundJobRun,
    *,
    status: JobRunStatus,
    detail: dict | None = None,
    error: str | None = None,
) -> None:
    run.status = status
    run.finished_at = datetime.now(UTC)
    if detail is not None:
        run.detail_json = json.dumps(detail, default=str)
    run.error_message = error
    session.commit()