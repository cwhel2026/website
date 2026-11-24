import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Territory(Base):
    __tablename__ = "territories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    minimum_job_value_gbp: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("250.00")
    )
    travel_cost_per_km_gbp: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), default=Decimal("0.45")
    )
    base_travel_charge_gbp: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00")
    )
    marketing_budget_monthly_gbp: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    localities: Mapped[list["TerritoryLocality"]] = relationship(
        back_populates="territory", cascade="all, delete-orphan"
    )
    postcode_districts: Mapped[list["PostcodeDistrict"]] = relationship(
        back_populates="territory", cascade="all, delete-orphan"
    )


class TerritoryLocality(Base):
    __tablename__ = "territory_localities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(120), index=True)

    territory: Mapped["Territory"] = relationship(back_populates="localities")


class PostcodeDistrict(Base):
    """Maps UK outward postcode district (e.g. L39, PR9) to a territory."""

    __tablename__ = "postcode_districts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    district: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="CASCADE")
    )

    territory: Mapped["Territory"] = relationship(back_populates="postcode_districts")