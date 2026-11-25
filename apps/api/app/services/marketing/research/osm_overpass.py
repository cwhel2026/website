"""OpenStreetMap Overpass — parking / retail / industrial features (ODbL, attribution required)."""

from __future__ import annotations

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


async def query_commercial_features(*, lat: float, lon: float, radius_m: int = 8000) -> dict:
    """Find amenity= parking, shop, industrial landuse near a point."""
    q = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{lat},{lon})["amenity"~"^(parking|fuel|car_wash)$"];
      way(around:{radius_m},{lat},{lon})["amenity"~"^(parking|fuel)$"];
      node(around:{radius_m},{lat},{lon})["shop"];
      way(around:{radius_m},{lat},{lon})["landuse"~"^(retail|commercial|industrial)$"];
    );
    out center 40;
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": q})
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        return {"ok": False, "message": str(exc)[:300], "items": []}
    items = []
    for el in data.get("elements") or []:
        tags = el.get("tags") or {}
        name = tags.get("name") or tags.get("operator") or "Unnamed feature"
        lat_c = el.get("lat") or (el.get("center") or {}).get("lat")
        lon_c = el.get("lon") or (el.get("center") or {}).get("lon")
        items.append(
            {
                "name": name,
                "feature_type": tags.get("amenity") or tags.get("shop") or tags.get("landuse"),
                "address_hint": tags.get("addr:street"),
                "postcode": tags.get("addr:postcode"),
                "website": tags.get("website"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "osm_id": f"{el.get('type')}/{el.get('id')}",
                "lat": lat_c,
                "lon": lon_c,
                "source": "OpenStreetMap via Overpass API",
                "source_url": f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
                "attribution": "© OpenStreetMap contributors",
            }
        )
    return {"ok": True, "items": items, "estimated_cost_usd": 0.0}