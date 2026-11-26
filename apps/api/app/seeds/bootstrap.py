from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.config import get_settings
from app.models.pricing import PricingProfile, PricingRule, PricingRuleType
from app.models.service import Service, ServiceCategory
from app.models.service import SurfaceType
from app.models.agents import AgentActionPermission, AgentProfile, OperatingMode
from app.models.finance import FreeAgentConnection, FreeAgentConnectionState, TaxYearSettings
from app.models.inventory import StockCategory, StockItem, Supplier
from app.models.marketing import AdPlatform, IntegrationState, MarketingIntegration
from app.models.communications import MessageCategory, MessageChannel, MessageTemplate
from app.models.scheduling import SchedulingSettings
from app.models.territory import PostcodeDistrict, Territory, TerritoryLocality
from app.models.user import User, UserRole
from app.models.weather import ProductProfile

settings = get_settings()

TERRITORIES = [
    {
        "code": "A",
        "name": "West Lancashire",
        "localities": [
            "Burscough",
            "Ormskirk",
            "Aughton",
            "Rufford",
            "Tarleton",
            "Hesketh Bank",
            "Parbold",
            "Skelmersdale",
            "Banks",
        ],
        "districts": ["L39", "L40", "WN8", "PR9", "PR26"],
    },
    {
        "code": "B",
        "name": "Sefton and Southport",
        "localities": [
            "Southport",
            "Ainsdale",
            "Birkdale",
            "Formby",
            "Freshfield",
            "Crosby",
            "Maghull",
            "Aintree",
        ],
        "districts": ["PR8", "PR9", "L23", "L31", "L22", "L21"],
    },
    {
        "code": "C",
        "name": "Liverpool and Merseyside",
        "localities": [
            "Liverpool",
            "Bootle",
            "West Derby",
            "Woolton",
            "Allerton",
            "Speke",
            "Kirkby",
            "Prescot",
            "Huyton",
            "St Helens",
        ],
        "districts": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24", "L25", "L26", "L27", "L28", "L29", "L30", "L31", "L32", "L33", "L34", "L35", "L36", "WA10", "WA11", "WA12"],
    },
    {
        "code": "D",
        "name": "Preston and Central Lancashire",
        "localities": [
            "Preston",
            "Penwortham",
            "Longton",
            "Leyland",
            "Bamber Bridge",
            "Lostock Hall",
            "Fulwood",
            "Garstang",
        ],
        "districts": ["PR1", "PR2", "PR3", "PR4", "PR5", "FY6"],
    },
    {
        "code": "E",
        "name": "Blackpool and Fylde Coast",
        "localities": [
            "Blackpool",
            "Lytham",
            "St Annes",
            "Poulton-le-Fylde",
            "Thornton-Cleveleys",
            "Fleetwood",
            "Kirkham",
            "Freckleton",
        ],
        "districts": ["FY1", "FY2", "FY3", "FY4", "FY5", "FY6", "FY7", "FY8"],
    },
    {
        "code": "F",
        "name": "Chorley and Wigan",
        "localities": [
            "Chorley",
            "Euxton",
            "Adlington",
            "Coppull",
            "Buckshaw Village",
            "Wigan",
            "Standish",
            "Shevington",
            "Orrell",
            "Ashton-in-Makerfield",
        ],
        "districts": ["PR6", "PR7", "WN1", "WN2", "WN3", "WN4", "WN5", "WN6"],
    },
    {
        "code": "G",
        "name": "Blackburn and East Lancashire",
        "localities": [
            "Blackburn",
            "Darwen",
            "Accrington",
            "Oswaldtwistle",
            "Great Harwood",
            "Rishton",
            "Clayton-le-Moors",
            "Clitheroe",
            "Whalley",
            "Burnley",
            "Padiham",
        ],
        "districts": ["BB1", "BB2", "BB3", "BB4", "BB5", "BB6", "BB7", "BB8", "BB9", "BB10", "BB11", "BB12"],
    },
    {
        "code": "H",
        "name": "Bolton and Greater Manchester",
        "localities": [
            "Bolton",
            "Horwich",
            "Westhoughton",
            "Farnworth",
            "Bury",
            "Manchester",
            "Salford",
            "Prestwich",
            "Trafford",
            "Eccles",
            "Worsley",
            "Swinton",
            "Sale",
            "Altrincham",
            "Stockport",
            "Rochdale",
            "Oldham",
        ],
        "districts": ["BL1", "BL2", "BL3", "BL4", "BL5", "BL6", "BL7", "BL8", "BL9", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24", "M25", "M26", "M27", "M28", "M29", "M30", "M31", "M32", "M33", "M34", "M35", "M38", "M40", "M41", "M43", "M44", "M45", "M46", "M50", "M60", "M61", "M90", "SK1", "SK2", "SK3", "SK4", "SK5", "SK6", "SK7", "SK8", "OL1", "OL2", "OL3", "OL4", "OL5", "OL6", "OL7", "OL8", "OL9", "OL10", "OL11", "OL12", "OL13", "OL14", "OL15", "OL16"],
    },
    {
        "code": "I",
        "name": "Warrington and surrounding areas",
        "localities": [
            "Warrington",
            "Newton-le-Willows",
            "Culcheth",
            "Lymm",
            "Widnes",
            "Runcorn",
        ],
        "districts": ["WA1", "WA2", "WA3", "WA4", "WA5", "WA6", "WA7", "WA8", "WA9", "WA13", "WA14", "WA15", "WA16"],
    },
]

SERVICES = [
    {
        "slug": "tarmac-driveway-restoration",
        "name": "Tarmac driveway restoration",
        "category": ServiceCategory.RESTORATION,
        "requires_washing": True,
        "requires_coating": True,
    },
    {
        "slug": "tarmac-recolouring",
        "name": "Tarmac recolouring",
        "category": ServiceCategory.RESTORATION,
        "requires_washing": True,
        "requires_coating": True,
    },
    {
        "slug": "block-paving-cleaning-sealing",
        "name": "Block paving cleaning, sanding and sealing",
        "category": ServiceCategory.RESTORATION,
        "requires_washing": True,
        "requires_coating": True,
    },
    {
        "slug": "imprinted-concrete-restoration",
        "name": "Pattern imprinted concrete restoration",
        "category": ServiceCategory.RESTORATION,
        "requires_washing": True,
        "requires_coating": True,
    },
    {
        "slug": "pressure-washing",
        "name": "Pressure washing",
        "category": ServiceCategory.CLEANING,
        "requires_washing": True,
        "requires_coating": False,
    },
    {
        "slug": "commercial-car-park-restoration",
        "name": "Commercial car park restoration",
        "category": ServiceCategory.COMMERCIAL,
        "requires_washing": True,
        "requires_coating": True,
        "is_commercial": True,
    },
    {
        "slug": "minor-tarmac-repairs",
        "name": "Minor tarmac repairs",
        "category": ServiceCategory.REPAIR,
        "requires_washing": False,
        "requires_coating": False,
    },
]


async def seed_database(session: AsyncSession) -> None:
    await _seed_admin(session)
    await _seed_territories(session)
    await _seed_services(session)
    await _seed_pricing(session)
    await _seed_scheduling(session)
    await _seed_product_profiles(session)
    await _seed_agents(session)
    await _seed_message_templates(session)
    await _seed_marketing_integrations(session)
    await _seed_finance(session)
    await _seed_inventory(session)
    await session.commit()


async def _seed_admin(session: AsyncSession) -> None:
    from app.services.owner_provisioning import ensure_owner_from_env

    await ensure_owner_from_env(session)


async def _seed_territories(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Territory))
    if count and count > 0:
        return
    assigned_districts: set[str] = set()
    for item in TERRITORIES:
        territory = Territory(
            code=item["code"],
            name=item["name"],
            description=f"Operating territory {item['code']} — {item['name']}",
            minimum_job_value_gbp=Decimal("275.00") if item["code"] in ("H", "C") else Decimal("250.00"),
        )
        session.add(territory)
        await session.flush()
        for loc in item["localities"]:
            session.add(TerritoryLocality(territory_id=territory.id, name=loc))
        for district in item["districts"]:
            if district in assigned_districts:
                continue
            assigned_districts.add(district)
            session.add(PostcodeDistrict(territory_id=territory.id, district=district))


async def _seed_services(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Service))
    if count and count > 0:
        return
    for idx, svc in enumerate(SERVICES):
        session.add(
            Service(
                slug=svc["slug"],
                name=svc["name"],
                description=f"Professional {svc['name'].lower()} across North West England.",
                category=svc["category"],
                requires_washing=svc.get("requires_washing", False),
                requires_coating=svc.get("requires_coating", False),
                is_commercial=svc.get("is_commercial", False),
                sort_order=idx,
            )
        )


async def _seed_pricing(session: AsyncSession) -> None:
    result = await session.execute(select(PricingProfile).limit(1))
    if result.scalar_one_or_none():
        return
    profile = PricingProfile(name="default", version=1, is_active=True)
    session.add(profile)
    await session.flush()
    rules = [
        (PricingRuleType.PER_SQM, SurfaceType.TARMAC, Decimal("16.50")),
        (PricingRuleType.PER_SQM, SurfaceType.BLOCK_PAVING, Decimal("14.00")),
        (PricingRuleType.PER_SQM, SurfaceType.IMPRINTED_CONCRETE, Decimal("17.50")),
        (PricingRuleType.MINIMUM_JOB, None, Decimal("250.00")),
        (PricingRuleType.WASHING_SURCHARGE, None, Decimal("2.50")),
        (PricingRuleType.COATING_SURCHARGE, None, Decimal("4.25")),
        (PricingRuleType.VAT_RATE, None, Decimal("20.00")),
        (PricingRuleType.MIN_CONTRIBUTION_MARGIN, None, Decimal("35.00")),
        (PricingRuleType.COMMERCIAL_MULTIPLIER, None, Decimal("1.30")),
    ]
    for rule_type, surface, amount in rules:
        session.add(
            PricingRule(
                profile_id=profile.id,
                rule_type=rule_type,
                surface_type=surface,
                amount_gbp=amount,
            )
        )


async def _seed_scheduling(session: AsyncSession) -> None:
    result = await session.execute(select(SchedulingSettings).limit(1))
    if result.scalar_one_or_none():
        return
    session.add(SchedulingSettings())


async def _seed_product_profiles(session: AsyncSession) -> None:
    result = await session.execute(select(ProductProfile).limit(1))
    if result.scalar_one_or_none():
        return
    session.add(
        ProductProfile(
            name="Default restoration coating (configure per manufacturer)",
            slug="default-restoration-coating",
            min_application_temp_c=Decimal("10"),
            max_application_temp_c=Decimal("28"),
            min_drying_hours=24,
            rain_free_window_hours=4,
            max_wind_mph=20,
            documentation_note=(
                "Placeholder profile for development. Replace with verified manufacturer "
                "datasheet values before production coating scheduling."
            ),
            is_active=True,
        )
    )


async def _seed_agents(session: AsyncSession) -> None:
    result = await session.execute(select(AgentProfile).limit(1))
    if result.scalar_one_or_none():
        return
    agents = [
        ("personal_assistant", "Personal Assistant"),
        ("scheduling", "Scheduling Agent"),
        ("weather", "Weather Intelligence Agent"),
        ("customer_service", "Customer Service Agent"),
        ("marketing", "Marketing Director"),
        ("finance", "Finance Agent"),
        ("business_director", "Business Director"),
    ]
    for slug, name in agents:
        session.add(
            AgentProfile(
                slug=slug,
                name=name,
                operating_mode=OperatingMode.SUPERVISED,
            )
        )
    permissions = [
        ("personal_assistant", "read_schedule", False, False),
        ("personal_assistant", "send_customer_message", False, True),
        ("customer_service", "send_enquiry_ack", True, False),
        ("customer_service", "send_customer_message", False, True),
        ("marketing", "ad_spend", False, True),
        ("finance", "sync_freeagent", False, True),
    ]
    for slug, action, controlled, approval in permissions:
        session.add(
            AgentActionPermission(
                agent_slug=slug,
                action_key=action,
                allowed_in_controlled=controlled,
                requires_approval=approval,
            )
        )


async def _seed_message_templates(session: AsyncSession) -> None:
    result = await session.execute(select(MessageTemplate).limit(1))
    if result.scalar_one_or_none():
        return
    templates = [
        (
            "enquiry_acknowledgement",
            "Enquiry acknowledgement",
            MessageChannel.EMAIL,
            MessageCategory.TRANSACTIONAL,
            "We received your enquiry — Revive My Drive",
            "Hello {{name}},\n\nThank you for contacting Revive My Drive about your {{surface}} driveway. "
            "We will review your details and respond shortly.\n\nRevive My Drive",
        ),
        (
            "quote_delivery",
            "Quotation delivery",
            MessageChannel.EMAIL,
            MessageCategory.TRANSACTIONAL,
            "Your provisional quotation {{reference}}",
            "Hello {{name}},\n\nYour provisional quotation {{reference}} is {{total}} inc. VAT. "
            "This remains subject to on-site verification.\n\nRevive My Drive",
        ),
        (
            "appointment_reminder",
            "Appointment reminder",
            MessageChannel.EMAIL,
            MessageCategory.TRANSACTIONAL,
            "Reminder: appointment on {{date}}",
            "Hello {{name}},\n\nThis is a reminder for your {{visit_type}} visit on {{date}}.\n\nRevive My Drive",
        ),
    ]
    for slug, name, channel, category, subject, body in templates:
        session.add(
            MessageTemplate(
                slug=slug,
                name=name,
                channel=channel,
                category=category,
                subject_template=subject,
                body_template=body,
            )
        )


async def _seed_inventory(session: AsyncSession) -> None:
    result = await session.execute(select(StockItem).limit(1))
    if result.scalar_one_or_none():
        return
    supplier = Supplier(name="Regional coatings supplier")
    session.add(supplier)
    await session.flush()
    session.add(
        StockItem(
            sku="COAT-TARMAC-20L",
            name="Tarmac restoration coating (20L)",
            category=StockCategory.COATING,
            unit="litre",
            quantity_on_hand=Decimal("40"),
            reorder_level=Decimal("15"),
            coverage_sqm_per_unit=Decimal("35"),
            wastage_allowance_pct=Decimal("10"),
            last_purchase_price_gbp=Decimal("185"),
            supplier_id=supplier.id,
        )
    )
    session.add(
        StockItem(
            sku="CHEM-ALGAE-5L",
            name="Algae remover concentrate (5L)",
            category=StockCategory.CHEMICAL,
            unit="litre",
            quantity_on_hand=Decimal("12"),
            reorder_level=Decimal("4"),
            coverage_sqm_per_unit=Decimal("80"),
            last_purchase_price_gbp=Decimal("42"),
            supplier_id=supplier.id,
        )
    )


async def _seed_finance(session: AsyncSession) -> None:
    result = await session.execute(select(TaxYearSettings).limit(1))
    if result.scalar_one_or_none() is None:
        session.add(
            TaxYearSettings(
                notes="Update allowances/rates from official HMRC publications when tax year changes.",
            )
        )
    fa = await session.execute(select(FreeAgentConnection).limit(1))
    if fa.scalar_one_or_none() is None:
        session.add(
            FreeAgentConnection(
                state=FreeAgentConnectionState.NOT_CONFIGURED,
            )
        )


async def _seed_marketing_integrations(session: AsyncSession) -> None:
    result = await session.execute(select(MarketingIntegration).limit(1))
    if result.scalar_one_or_none():
        return
    for platform in (AdPlatform.META, AdPlatform.GOOGLE):
        session.add(
            MarketingIntegration(
                platform=platform,
                state=IntegrationState.NOT_CONFIGURED,
                config_note="No credentials configured — simulation mode only",
            )
        )