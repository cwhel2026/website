import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SurfaceType(str, enum.Enum):
    TARMAC = "tarmac"
    BLOCK_PAVING = "block_paving"
    IMPRINTED_CONCRETE = "imprinted_concrete"
    CONCRETE = "concrete"
    OTHER = "other"


class ServiceCategory(str, enum.Enum):
    RESTORATION = "restoration"
    CLEANING = "cleaning"
    REPAIR = "repair"
    COMMERCIAL = "commercial"


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[ServiceCategory] = mapped_column(
        Enum(ServiceCategory, name="service_category")
    )
    surface_types: Mapped[str] = mapped_column(
        String(255), default="tarmac,block_paving,imprinted_concrete"
    )
    requires_washing: Mapped[bool] = mapped_column(default=False)
    requires_coating: Mapped[bool] = mapped_column(default=False)
    is_commercial: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )