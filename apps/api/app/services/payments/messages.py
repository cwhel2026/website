"""Pure message rendering; no external communication or payment side effects."""
from decimal import Decimal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from app.models.jobs import AppointmentStatus, AppointmentType

LONDON = ZoneInfo("Europe/London")


def deposit_message(customer_name: str, reference: str, amount_pence: int, url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Secure payment link required")
    if amount_pence <= 0:
        raise ValueError("Positive deposit required")
    return (
        f"Hi {customer_name}, your SurfaceCoat booking reference is {reference}. "
        f"Your booking deposit is £{Decimal(amount_pence) / 100:,.2f}. "
        f"Please use this secure payment link: {url}\n\n"
        "Your appointment will be confirmed once payment has been received. "
        "The deposit will be deducted from your final balance. Thank you, SurfaceCoat."
    )


def booking_confirmation(customer_name: str, reference: str, address: str,
                         service: str, appointments, *, two_stage: bool) -> tuple[str, str]:
    if not address.strip() or not service.strip():
        raise ValueError("Booking address and service required")
    confirmed = [a for a in appointments if a.status == AppointmentStatus.CONFIRMED]
    if not confirmed:
        raise ValueError("Confirmed appointment required")
    lines = [f"Hi {customer_name},", "", "Thank you. Your booking deposit has been received.",
             f"Booking reference: {reference}", f"Service: {service}", f"Address: {address}", ""]
    for a in sorted(confirmed, key=lambda a: a.scheduled_start):
        start = a.scheduled_start.astimezone(LONDON)
        end = a.scheduled_end.astimezone(LONDON)
        lines.append(f"{a.appointment_type.value.replace('_', ' ').title()}: "
                     f"{start:%A %d %B %Y, %H:%M} to {end:%H:%M %Z}")
    if two_stage and not any(a.appointment_type == AppointmentType.COATING for a in confirmed):
        lines.append("Coating will be arranged within seven days of washing, subject to weather and surface drying.")
    lines.extend(["", "Your deposit will be deducted from your final balance.", "Thank you, SurfaceCoat"])
    return f"SurfaceCoat booking confirmation - {reference}", "\n".join(lines)
