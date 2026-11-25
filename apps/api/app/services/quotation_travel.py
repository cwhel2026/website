"""Server-side travel distance from the operational base (not client-supplied)."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.geo import haversine_km
from app.services.geocode import geocode_postcode
from app.services.scheduling_engine import get_scheduling_settings


async def travel_km_from_base(db: AsyncSession, postcode: str) -> Decimal:
    settings = await get_scheduling_settings(db)
    base_lat = float(settings.base_latitude)
    base_lon = float(settings.base_longitude)
    point = await geocode_postcode(postcode)
    return haversine_km(base_lat, base_lon, point.latitude, point.longitude)