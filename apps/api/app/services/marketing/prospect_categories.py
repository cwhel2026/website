"""Commercial vertical search templates — no fabricated data."""

PROSPECT_VERTICALS: dict[str, list[str]] = {
    "supermarket": ["supermarket car park {area}", "grocery store parking {area}"],
    "retail_park": ["retail park {area}", "shopping centre car park {area}"],
    "industrial": ["industrial estate {area}", "warehouse {area}"],
    "business_park": ["business park {area}", "office park parking {area}"],
    "hotel": ["hotel car park {area}"],
    "hospitality": ["pub car park {area}", "restaurant parking {area}"],
    "car_dealership": ["car dealership {area}"],
    "petrol_station": ["petrol station forecourt {area}", "fuel station {area}"],
    "housing_association": ["housing association {area}"],
    "leisure": ["leisure centre car park {area}", "gym car park {area}"],
}

TERRITORY_AREAS = [
    "Blackpool",
    "Preston",
    "Southport",
    "Liverpool",
    "Manchester",
    "Blackburn",
    "Accrington",
    "Chorley",
    "Wigan",
    "Bolton",
    "Warrington",
    "Burnley",
    "Lancashire",
]


def vertical_places_queries(vertical: str, area: str) -> list[str]:
    templates = PROSPECT_VERTICALS.get(vertical, [f"car park {area}"])
    return [t.format(area=area) for t in templates]