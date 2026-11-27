"""Find-or-create customers and properties without duplicating existing rows."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Customer, CustomerProperty


def compact_postcode(postcode: str) -> str:
    return "".join(postcode.upper().split())


def compact_address(line: str) -> str:
    return " ".join(line.lower().split())


async def upsert_customer(
    db: AsyncSession,
    *,
    email: str,
    phone: str | None,
    full_name: str,
    consent_marketing: bool = False,
    consent_service_messages: bool = True,
    source: str | None = None,
    campaign: str | None = None,
) -> Customer:
    result = await db.execute(
        select(Customer).where(func.lower(Customer.email) == email.strip().lower())
    )
    customer = result.scalar_one_or_none()
    if customer:
        customer.full_name = full_name
        if phone:
            customer.phone = phone
        if source:
            customer.source = source
        if campaign:
            customer.campaign = campaign
        customer.consent_marketing = consent_marketing
        customer.consent_service_messages = consent_service_messages
        return customer
    customer = Customer(
        email=email.strip(),
        phone=phone,
        full_name=full_name,
        consent_marketing=consent_marketing,
        consent_service_messages=consent_service_messages,
        source=source,
        campaign=campaign,
    )
    db.add(customer)
    await db.flush()
    return customer


async def ensure_property(
    db: AsyncSession,
    *,
    customer: Customer,
    address_line1: str,
    address_line2: str | None,
    town: str,
    postcode: str,
    territory_id,
    latitude: float | None = None,
    longitude: float | None = None,
) -> CustomerProperty:
    """Reuse the same property when the customer already has this address."""
    wanted_pc = compact_postcode(postcode)
    wanted_line = compact_address(address_line1)
    result = await db.execute(
        select(CustomerProperty).where(CustomerProperty.customer_id == customer.id)
    )
    for prop in result.scalars().all():
        if compact_postcode(prop.postcode) == wanted_pc and compact_address(prop.address_line1) == wanted_line:
            prop.town = town
            if address_line2:
                prop.address_line2 = address_line2
            if territory_id:
                prop.territory_id = territory_id
            if latitude is not None:
                prop.latitude = latitude
            if longitude is not None:
                prop.longitude = longitude
            return prop
    prop = CustomerProperty(
        customer_id=customer.id,
        address_line1=address_line1.strip(),
        address_line2=address_line2,
        town=town,
        postcode=postcode.upper().strip(),
        territory_id=territory_id,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(prop)
    await db.flush()
    return prop
