import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_APPROVAL = "awaiting_approval"


class AgentTask(Base):
    """Structured work queue for AI / automation — no uncontrolled agent loops."""

    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_slug: Mapped[str] = mapped_column(String(60), index=True)
    assigned_by: Mapped[str] = mapped_column(String(60), default="business_director")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="agent_task_status"), default=TaskStatus.QUEUED
    )
    priority: Mapped[int] = mapped_column(Integer, default=50)
    action_key: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(255))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    max_iterations: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)