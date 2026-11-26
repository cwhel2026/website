"""AI marketing content generation with spend controls."""

from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.marketing_ops import ContentPlatform, ContentStatus, MarketingContentItem
from app.services.ai.usage_limits import check_spend_allowed, estimate_openai_cost_gbp, record_usage
from app.services.marketing.brand_profile import brand_system_prompt, get_or_create_brand


async def _brand_system(db: AsyncSession) -> str:
    brand = await get_or_create_brand(db)
    return brand_system_prompt(brand)


async def _generate_text(db: AsyncSession, prompt: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return (
            f"[Draft — configure OPENAI_API_KEY]\n\n"
            f"Revive My Drive Ltd — {prompt[:400]}\n\n"
            "Request your free quotation at revivemydrive.co.uk"
        )
    allowed, _ = await check_spend_allowed(db)
    if not allowed:
        return "Daily AI spend limit reached — edit this draft manually."
    model = settings.openai_model
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": await _brand_system(db),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    usage = data.get("usage") or {}
    cost = estimate_openai_cost_gbp(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), model)
    await record_usage(
        db,
        provider="openai",
        model=model,
        agent_slug="marketing_content",
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        estimated_cost_gbp=cost,
    )
    return (data["choices"][0]["message"]["content"] or "").strip()


async def generate_platform_content(
    db: AsyncSession,
    *,
    platform: ContentPlatform,
    brief: str,
    territory_name: str | None = None,
) -> MarketingContentItem:
    prompt = (
        f"Write a {platform.value} post for Revive My Drive Ltd (driveway/tarmac/block paving restoration, "
        f"North West England). Brief: {brief}. "
    )
    if territory_name:
        prompt += f"Mention {territory_name} naturally once. "
    prompt += (
        "No fake reviews, no invented before/after claims, no guaranteed savings. "
        "Include a call to request a quotation on revivemydrive.co.uk."
    )
    text = await _generate_text(db, prompt)
    item = MarketingContentItem(
        platform=platform,
        title=brief[:255] or f"{platform.value} draft",
        body_text=text,
        status=ContentStatus.PENDING_APPROVAL,
    )
    db.add(item)
    await db.flush()
    return item