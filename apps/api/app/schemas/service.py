from uuid import UUID

from app.models.service import ServiceCategory
from app.schemas.common import ORMModel


class ServiceOut(ORMModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    category: ServiceCategory
    surface_types: str
    requires_washing: bool
    requires_coating: bool
    is_commercial: bool
    is_active: bool