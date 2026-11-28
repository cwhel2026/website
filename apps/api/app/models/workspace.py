from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WorkspaceConnection(Base):
    __tablename__ = "workspace_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    oauth_state_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    oauth_verifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
