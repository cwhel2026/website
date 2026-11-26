import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class BackgroundJobRun(Base):
    __tablename__ = "background_job_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_name: Mapped[str] = mapped_column(String(80), index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[JobRunStatus] = mapped_column(
        Enum(JobRunStatus, name="job_run_status"), default=JobRunStatus.PENDING
    )
    worker_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SchedulerHeartbeat(Base):
    """Liveness rows written by the Celery beat/worker process (one row per component)."""

    __tablename__ = "scheduler_heartbeats"

    component: Mapped[str] = mapped_column(String(40), primary_key=True)
    hostname: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_beat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail_json: Mapped[str] = mapped_column(Text, default="{}")