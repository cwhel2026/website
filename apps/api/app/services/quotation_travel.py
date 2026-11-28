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

async def road_travel_from_base(db: AsyncSession, postcode: str) -> tuple[Decimal, Decimal]:
    """OSRM-compatible road routing; never silently substitute straight-line travel."""
    import os
    import httpx
    from fastapi import HTTPException

    endpoint = os.environ.get("QUOTATION_ROUTING_URL", "").rstrip("/")
    if not endpoint:
        raise HTTPException(503, "Road routing is temporarily unavailable. Please contact us for an estimate.")
    settings = await get_scheduling_settings(db)
    point = await geocode_postcode(postcode)
    coordinates = f"{settings.base_longitude},{settings.base_latitude};{point.longitude},{point.latitude}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{endpoint}/route/v1/driving/{coordinates}", params={"overview": "false"})
            response.raise_for_status()
            payload = response.json()
        if payload.get("code") != "Ok":
            raise ValueError("No route")
        route = payload["routes"][0]
        km = Decimal(str(route["distance"])) / 1000
        hours = Decimal(str(route["duration"])) / 3600
        if not km.is_finite() or not hours.is_finite() or min(km, hours) < 0:
            raise ValueError("Invalid route")
        return km, hours
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, ArithmeticError) as exc:
        raise HTTPException(503, "Road routing is temporarily unavailable. Please contact us for an estimate.") from exc
