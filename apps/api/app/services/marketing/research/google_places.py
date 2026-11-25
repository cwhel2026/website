"""Google Places API — commercial premises discovery (legitimate API only)."""

from __future__ import annotations

from urllib.parse import quote

import httpx

from app.config import get_settings

PLACES_COST_PER_SEARCH_USD = 0.032


async def search_places(*, query: str, latitude: float | None = None, longitude: float | None = None) -> dict:
    key = get_settings().google_places_api_key
    if not key:
        return {"ok": False, "message": "GOOGLE_PLACES_API_KEY not configured", "items": []}
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.types,"
            "places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.location"
        ),
    }
    body: dict = {"textQuery": query, "maxResultCount": 20, "languageCode": "en"}
    if latitude is not None and longitude is not None:
        body["locationBias"] = {
            "circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": 20000.0}
        }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        return {"ok": False, "message": str(exc)[:300], "items": []}
    items = []
    for p in data.get("places") or []:
        items.append(
            {
                "place_id": p.get("id", "").split("/")[-1],
                "name": (p.get("displayName") or {}).get("text"),
                "address": p.get("formattedAddress"),
                "types": p.get("types") or [],
                "phone": p.get("nationalPhoneNumber"),
                "website": p.get("websiteUri"),
                "maps_url": p.get("googleMapsUri"),
                "source": "Google Places API (New)",
                "source_url": p.get("googleMapsUri") or f"https://www.google.com/maps/search/?api=1&query={quote(query)}",
            }
        )
    return {
        "ok": True,
        "items": items,
        "estimated_cost_usd": PLACES_COST_PER_SEARCH_USD,
        "source": "https://developers.google.com/maps/documentation/places/web-service",
    }