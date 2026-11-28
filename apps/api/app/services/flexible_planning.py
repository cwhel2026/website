"""Read-only area matching; never reserves appointments or changes prices."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import CustomerProperty, Enquiry, PipelineStage
from app.models.jobs import Appointment, AppointmentStatus, Job, JobStatus
from app.models.quotation import Quotation, QuotationStatus
from app.services.geo import haversine_km


def discount_review(subtotal, contribution, travel):
    """Conservative headroom with no unverified travel savings credited."""
    subtotal, contribution, travel = map(Decimal, (subtotal, contribution, travel))
    floor = Decimal("0.35")
    headroom = max(Decimal(0), (contribution - floor * subtotal) / (1 - floor))
    return {
        "estimated_travel_cost_gbp": str(travel),
        "illustrative_max_discount_ex_vat_gbp": str(min(headroom, max(Decimal(0), travel)).quantize(Decimal("0.01"), rounding="ROUND_DOWN")),
        "basis": "Illustrative 35% contribution floor, no assumed travel savings; verify actual costs, VAT and company margin policy before agreeing any discount.",
    }


async def flexible_opportunities(db: AsyncSession):
    now = datetime.now(UTC)
    leads = (await db.execute(
        select(Enquiry, Quotation, CustomerProperty)
        .join(Quotation, Quotation.enquiry_id == Enquiry.id)
        .join(CustomerProperty, CustomerProperty.id == Quotation.property_id)
        .where(Enquiry.intention == "flexible_booking", Enquiry.is_test.is_(False),
               Enquiry.stage.in_([PipelineStage.BOOKING_PENDING, PipelineStage.REGIONAL_WAITING_LIST, PipelineStage.QUOTE_GENERATED]),
               Quotation.is_test.is_(False),
               Quotation.status.in_([QuotationStatus.PROVISIONAL, QuotationStatus.SENT, QuotationStatus.PENDING_APPROVAL]),
               ~select(Job.id).where(Job.quotation_id == Quotation.id, Job.status != JobStatus.CANCELLED).exists())
        .order_by(Enquiry.created_at).limit(100)
    )).all()
    visits = (await db.execute(
        select(Appointment, Job).join(Job)
        .join(Quotation, Quotation.id == Job.quotation_id)
        .where(Appointment.status == AppointmentStatus.CONFIRMED,
               Appointment.scheduled_start >= now, Appointment.scheduled_start < now + timedelta(days=14),
               Job.status != JobStatus.CANCELLED, Quotation.is_test.is_(False))
        .order_by(Appointment.scheduled_start).limit(200)
    )).all()
    matches = []
    for enquiry, quote, prop in leads:
        if prop.latitude is None or prop.longitude is None:
            continue
        for visit, job in visits:
            if visit.latitude is None or visit.longitude is None or visit.weather_suitable is False:
                continue
            distance = haversine_km(prop.latitude, prop.longitude, visit.latitude, visit.longitude)
            if distance > Decimal("8.04672"):
                continue
            matches.append({
                "reference": quote.reference, "town": prop.town, "postcode": prop.postcode,
                "nearby_job": job.reference, "nearby_visit_start": visit.scheduled_start.isoformat(),
                "nearby_visit_type": visit.appointment_type.value,
                "straight_line_km": str(distance), "original_total_gbp": str(quote.total_inc_vat_gbp),
                "nearby_visit_weather_flag": visit.weather_suitable,
                "discount_review": discount_review(quote.subtotal_ex_vat_gbp, quote.estimated_contribution_gbp, quote.estimated_travel_gbp),
            })
    matches.sort(key=lambda item: (Decimal(item["straight_line_km"]), item["nearby_visit_start"]))
    return {"open_flexible_quotes_scanned": len(leads), "confirmed_visits_scanned": len(visits),
            "matches": matches[:20], "radius_miles": 5,
            "warning": "Area leads only, not available slots. Check actual route, capacity, live weather, drying and both visits before contacting or booking. Missing coordinates are excluded. No discount or booking has been authorised."}
