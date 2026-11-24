from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_usage import AiUsageEvent

settings = get_settings()


async def check_spend_allowed(db: AsyncSession) -> tuple[bool, str]:
    since = datetime.now(UTC) - timedelta(days=1)
    spent = await db.scalar(
        select(func.coalesce(func.sum(AiUsageEvent.estimated_cost_gbp), 0)).where(
            AiUsageEvent.created_at >= since
        )
    )
    spent_dec = Decimal(str(spent or 0))
    limit = settings.ai_daily_spend_limit_gbp
    if spent_dec >= limit:
        return False, f"Daily AI spend limit reached (£{limit})."
    return True, "OK"


def estimate_openai_cost_gbp(prompt_tokens: int, completion_tokens: int, model: str) -> Decimal:
    """Rough list prices — monitor only, not billing."""
    if "gpt-4" in model:
        rate_in, rate_out = Decimal("0.000004"), Decimal("0.000012")
    else:
        rate_in, rate_out = Decimal("0.0000004"), Decimal("0.0000012")
    cost = Decimal(prompt_tokens) * rate_in + Decimal(completion_tokens) * rate_out
    return cost.quantize(Decimal("0.0001"))


async def record_usage(
    db: AsyncSession,
    *,
    provider: str,
    model: str,
    agent_slug: str,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost_gbp: Decimal,
) -> None:
    db.add(
        AiUsageEvent(
            provider=provider,
            model=model,
            agent_slug=agent_slug,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_gbp=estimated_cost_gbp,
        )
    )