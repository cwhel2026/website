"""UK postcode geocoding via postcodes.io (permitted public API)."""

from dataclasses import dataclass

import httpx

from fastapi import HTTPException


@dataclass
class GeoPoint:
    latitude: float
    longitude: float
    postcode: str
    source: str = "postcodes.io"


async def geocode_postcode(postcode: str) -> GeoPoint:
    clean = postcode.strip().upper().replace(" ", "")
    spaced = clean if len(clean) <= 4 else f"{clean[:-3]} {clean[-3:]}"
    url = f"https://api.postcodes.io/postcodes/{spaced.replace(' ', '%20')}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Postcode not found")
            response.raise_for_status()
            data = response.json().get("result") or {}
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Postcode lookup is temporarily unavailable. Try again in a few minutes.",
        ) from exc
    return GeoPoint(
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        postcode=str(data.get("postcode", spaced)),
    )