"""Map local expense categories to FreeAgent category URLs from cache."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.finance import ExpenseCategory
from app.models.freeagent_cache import FreeAgentResourceCache

_HINTS: dict[ExpenseCategory, tuple[str, ...]] = {
    ExpenseCategory.FUEL: ("travel", "motor", "fuel"),
    ExpenseCategory.MATERIALS: ("cost of sales", "material", "hardware"),
    ExpenseCategory.ADVERTISING: ("advert", "marketing"),
    ExpenseCategory.EQUIPMENT: ("equipment", "asset", "tools"),
    ExpenseCategory.INSURANCE: ("insurance",),
    ExpenseCategory.PROFESSIONAL: ("legal", "accounting", "professional"),
    ExpenseCategory.OTHER: ("general", "sundry", "office"),
}


async def resolve_category_url(db: AsyncSession, category: ExpenseCategory) -> str | None:
    settings = get_settings()
    if settings.freeagent_default_expense_category_url:
        return settings.freeagent_default_expense_category_url

    result = await db.execute(
        select(FreeAgentResourceCache).where(FreeAgentResourceCache.resource_key == "categories_cache")
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    payload = json.loads(row.payload_json)
    categories = payload.get("categories") or []
    hints = _HINTS.get(category, _HINTS[ExpenseCategory.OTHER])
    for cat in categories:
        name = str(cat.get("description") or cat.get("name") or "").lower()
        url = cat.get("url")
        if not url:
            continue
        if any(h in name for h in hints):
            return str(url)
    for cat in categories:
        url = cat.get("url")
        if url:
            return str(url)
    return None