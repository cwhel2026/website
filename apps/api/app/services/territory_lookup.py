import re
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.territory import PostcodeDistrict, Territory, TerritoryLocality

UK_POSTCODE_RE = re.compile(
    r"^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*\d[A-Z]{2}$", re.IGNORECASE
)


def extract_outward_postcode(postcode: str) -> str | None:
    normalized = postcode.strip().upper().replace("  ", " ")
    if " " not in normalized and len(normalized) >= 4:
        normalized = normalized[:-3] + " " + normalized[-3:]
    match = UK_POSTCODE_RE.match(normalized)
    if not match:
        return None
    return match.group(1).upper()


async def resolve_territory_for_postcode(
    db: AsyncSession, postcode: str, town: str | None = None
) -> Territory | None:
    outward = extract_outward_postcode(postcode)
    if outward:
        result = await db.execute(
            select(Territory)
            .join(PostcodeDistrict)
            .where(PostcodeDistrict.district == outward, Territory.is_active.is_(True))
        )
        territory = result.scalar_one_or_none()
        if territory:
            return territory

    if town:
        town_clean = town.strip()
        result = await db.execute(
            select(Territory)
            .join(TerritoryLocality)
            .where(
                Territory.is_active.is_(True),
                or_(
                    func.lower(TerritoryLocality.name) == town_clean.lower(),
                    func.lower(TerritoryLocality.name).like(f"{town_clean.lower()}%"),
                ),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
    return None


async def get_territory_by_id(db: AsyncSession, territory_id: UUID) -> Territory | None:
    result = await db.execute(
        select(Territory).where(Territory.id == territory_id, Territory.is_active.is_(True))
    )
    return result.scalar_one_or_none()