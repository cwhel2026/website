from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class HourForecast:
    forecast_time: datetime
    temp_c: Decimal
    precipitation_mm: Decimal
    precip_probability_pct: int
    wind_mph: int
    humidity_pct: int