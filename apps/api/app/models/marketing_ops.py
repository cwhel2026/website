"""Stage 7 — marketing operations models (budgets, prospects, content, outreach)."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.marketing import OutreachStatus


class ContentPlatform(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE_BUSINESS = "google_business"
    WEBSITE = "website"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"


class OutreachMessageStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    SUPPRESSED = "suppressed"
    FAILED = "failed"


class MarketingBudgetPolicy(Base):
    """Owner-configurable spending limits — live ads blocked until explicitly approved."""

    __tablename__ = "marketing_budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    live_paid_spend_approved: Mapped[bool] = mapped_column(default=False)
    emergency_pause_all: Mapped[bool] = mapped_column(default=False)
    daily_limit_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    weekly_limit_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    monthly_limit_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    meta_daily_limit_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    google_daily_limit_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    max_single_increase_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CommercialProspect(Base):
    __tablename__ = "commercial_prospects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dedupe_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    business_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    site_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_name: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    opportunity_category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    outreach_status: Mapped[OutreachStatus] = mapped_column(
        Enum(OutreachStatus, name="outreach_status", create_constraint=False),
        default=OutreachStatus.NEW,
    )
    lawful_basis: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_corporate_subscriber: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    opt_out: Mapped[bool] = mapped_column(default=False)
    evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commercial_prospects.id", ondelete="CASCADE")
    )
    subject: Mapped[str] = mapped_column(String(255))
    body_text: Mapped[str] = mapped_column(Text)
    status: Mapped[OutreachMessageStatus] = mapped_column(
        Enum(OutreachMessageStatus, name="outreach_message_status"),
        default=OutreachMessageStatus.DRAFT,
    )
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MarketingMediaAsset(Base):
    __tablename__ = "marketing_media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    content_sha256: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(80), default="image/jpeg")
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="upload")
    customer_permission: Mapped[bool] = mapped_column(default=False)
    is_ai_generated: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MarketingContentItem(Base):
    __tablename__ = "marketing_content_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[ContentPlatform] = mapped_column(Enum(ContentPlatform, name="content_platform"))
    title: Mapped[str] = mapped_column(String(255))
    body_text: Mapped[str] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"), default=ContentStatus.DRAFT
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    media_asset_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    publish_external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    publish_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TerritoryIntelligenceScore(Base):
    __tablename__ = "territory_intelligence_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), unique=True
    )
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0)
    demand_indicator: Mapped[int] = mapped_column(Integer, default=0)
    competition_indicator: Mapped[int] = mapped_column(Integer, default=0)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )