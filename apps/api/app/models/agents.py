import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperatingMode(str, enum.Enum):
    MANUAL = "manual"
    SUPERVISED = "supervised"
    CONTROLLED = "controlled"


class AgentSlug(str, enum.Enum):
    BUSINESS_DIRECTOR = "business_director"
    PERSONAL_ASSISTANT = "personal_assistant"
    SCHEDULING = "scheduling"
    WEATHER = "weather"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"
    FINANCE = "finance"


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    operating_mode: Mapped[OperatingMode] = mapped_column(
        Enum(OperatingMode, name="operating_mode"), default=OperatingMode.SUPERVISED
    )
    is_paused: Mapped[bool] = mapped_column(default=False)
    emergency_stop: Mapped[bool] = mapped_column(default=False)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AgentActionPermission(Base):
    __tablename__ = "agent_action_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_slug: Mapped[str] = mapped_column(String(60), index=True)
    action_key: Mapped[str] = mapped_column(String(80))
    allowed_in_controlled: Mapped[bool] = mapped_column(default=False)
    requires_approval: Mapped[bool] = mapped_column(default=True)
    daily_limit: Mapped[int | None] = mapped_column(nullable=True)