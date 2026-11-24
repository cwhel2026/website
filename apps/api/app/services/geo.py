import math
from decimal import Decimal


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> Decimal:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Decimal(str(round(r * c, 2)))


def estimate_drive_minutes(distance_km: Decimal, avg_speed_kmh: Decimal = Decimal("45")) -> int:
    if distance_km <= 0:
        return 0
    hours = float(distance_km) / float(avg_speed_kmh)
    return max(1, int(hours * 60))