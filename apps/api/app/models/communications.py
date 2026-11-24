import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PORTAL = "portal"


class MessageCategory(str, enum.Enum):
    TRANSACTIONAL = "transactional"
    PROMOTIONAL = "promotional"


class OutboundStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    channel: Mapped[MessageChannel] = mapped_column(Enum(MessageChannel, name="message_channel"))
    category: Mapped[MessageCategory] = mapped_column(
        Enum(MessageCategory, name="message_category")
    )
    subject_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class OutboundMessage(Base):
    __tablename__ = "outbound_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    template_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    channel: Mapped[MessageChannel] = mapped_column(Enum(MessageChannel, name="message_channel"))
    category: Mapped[MessageCategory] = mapped_column(
        Enum(MessageCategory, name="message_category")
    )
    status: Mapped[OutboundStatus] = mapped_column(
        Enum(OutboundStatus, name="outbound_status"), default=OutboundStatus.DRAFT
    )
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)