import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdPlatform(str, enum.Enum):
    META = "meta"
    GOOGLE = "google"
    FLYER = "flyer"
    ORGANIC = "organic"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    LIVE_SIMULATED = "live_simulated"
    LIVE = "live"
    PAUSED = "paused"
    ENDED = "ended"


class OutreachStatus(str, enum.Enum):
    NEW = "new"
    RESEARCHED = "researched"
    READY_TO_CONTACT = "ready_to_contact"
    CONTACTED = "contacted"
    REPLIED = "replied"
    NOT_SUITABLE = "not_suitable"
    SUPPRESSED = "suppressed"


class FlyerCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ORDER_PACK_READY = "order_pack_ready"
    DISTRIBUTED = "distributed"
    CANCELLED = "cancelled"


class IntegrationState(str, enum.Enum):
    NOT_CONFIGURED = "not_configured"
    SANDBOX = "sandbox"
    CONNECTED = "connected"
    ERROR = "error"


class RegionalCampaign(Base):
    __tablename__ = "regional_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[AdPlatform] = mapped_column(Enum(AdPlatform, name="ad_platform"))
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    service_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"), default=CampaignStatus.DRAFT
    )
    simulation_only: Mapped[bool] = mapped_column(default=True)
    daily_budget_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    monthly_budget_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    spent_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    landing_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_campaign_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CommercialLead(Base):
    __tablename__ = "commercial_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    town: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    lead_source: Mapped[str] = mapped_column(String(80), default="manual")
    outreach_status: Mapped[OutreachStatus] = mapped_column(
        Enum(OutreachStatus, name="outreach_status"), default=OutreachStatus.NEW
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    is_corporate_subscriber: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    opt_out: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FlyerCampaign(Base):
    __tablename__ = "flyer_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id"), nullable=True
    )
    postcode_targets: Mapped[str] = mapped_column(Text, default="")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    print_cost_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    distribution_cost_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    qr_slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    landing_path: Mapped[str] = mapped_column(String(255))
    status: Mapped[FlyerCampaignStatus] = mapped_column(
        Enum(FlyerCampaignStatus, name="flyer_campaign_status"),
        default=FlyerCampaignStatus.DRAFT,
    )
    distribution_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AttributionEvent(Base):
    __tablename__ = "attribution_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    enquiry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_campaigns.id"), nullable=True
    )
    flyer_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flyer_campaigns.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(80))
    medium: Mapped[str] = mapped_column(String(80), default="unknown")
    content: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(80), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(120), nullable=True)
    landed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MarketingIntegration(Base):
    __tablename__ = "marketing_integrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[AdPlatform] = mapped_column(
        Enum(AdPlatform, name="ad_platform", create_constraint=False), unique=True
    )
    state: Mapped[IntegrationState] = mapped_column(
        Enum(IntegrationState, name="integration_state"), default=IntegrationState.NOT_CONFIGURED
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_note: Mapped[str | None] = mapped_column(Text, nullable=True)