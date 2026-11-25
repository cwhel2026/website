"""Rule-based transaction categorisation with confidence scores — no silent ledger changes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BankTransaction, ExpenseCategory


@dataclass(frozen=True)
class CategorisationSuggestion:
    category: ExpenseCategory
    confidence: int
    explanation: str
    is_personal: bool
    receipt_required: bool
    vat_likely: bool
    possible_duplicate: bool


_PERSONAL_HINTS = re.compile(
    r"\b(amazon\s*prime|netflix|spotify|tesco\s*personal|asda(?!\s*(trade|business)))\b",
    re.I,
)

_RULES: list[tuple[re.Pattern[str], ExpenseCategory, int, str]] = [
    (re.compile(r"\b(shell|bp|esso|texaco|fuel|petrol|diesel)\b", re.I), ExpenseCategory.FUEL, 88, "Fuel retailer name"),
    (re.compile(r"\b(screwfix|travis|wickes|jewson|buildbase)\b", re.I), ExpenseCategory.MATERIALS, 85, "Trade merchant"),
    (re.compile(r"\b(google\s*ads|facebook|meta\s*ads|advertising)\b", re.I), ExpenseCategory.ADVERTISING, 82, "Advertising spend"),
    (re.compile(r"\b(insurance|axa|aviva|zurich)\b", re.I), ExpenseCategory.INSURANCE, 80, "Insurance provider"),
    (re.compile(r"\b(accountant|bookkeeper|freeagent)\b", re.I), ExpenseCategory.PROFESSIONAL, 78, "Professional services"),
    (re.compile(r"\b(hire|rental|tool\s*station)\b", re.I), ExpenseCategory.EQUIPMENT, 75, "Equipment / hire"),
]


def suggest_for_description(description: str, amount_gbp: Decimal) -> CategorisationSuggestion:
    text = description.strip()
    is_outflow = amount_gbp < 0
    personal = bool(_PERSONAL_HINTS.search(text))
    receipt_required = is_outflow and abs(amount_gbp) >= Decimal("25")
    vat_likely = is_outflow and abs(amount_gbp) >= Decimal("10")

    best: CategorisationSuggestion | None = None
    for pattern, category, base_conf, reason in _RULES:
        if pattern.search(text):
            conf = base_conf
            if personal:
                conf = min(conf, 55)
            best = CategorisationSuggestion(
                category=category,
                confidence=conf,
                explanation=f"{reason} in «{text[:80]}».",
                is_personal=personal,
                receipt_required=receipt_required,
                vat_likely=vat_likely,
                possible_duplicate=False,
            )
            break

    if best:
        return best

    default_cat = ExpenseCategory.OTHER
    conf = 45 if is_outflow else 35
    return CategorisationSuggestion(
        category=default_cat,
        confidence=conf,
        explanation=(
            "No strong merchant keyword match — please confirm category."
            if is_outflow
            else "Money in — may be customer payment; match to invoice if applicable."
        ),
        is_personal=personal,
        receipt_required=receipt_required,
        vat_likely=vat_likely,
        possible_duplicate=False,
    )


async def flag_possible_duplicates(
    db: AsyncSession, txn: BankTransaction, window_days: int = 3
) -> bool:
    from datetime import timedelta

    if txn.transacted_at is None:
        return False
    start = txn.transacted_at - timedelta(days=window_days)
    end = txn.transacted_at + timedelta(days=window_days)
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.id != txn.id,
            BankTransaction.amount_gbp == txn.amount_gbp,
            BankTransaction.transacted_at >= start,
            BankTransaction.transacted_at <= end,
        )
    )
    return result.scalars().first() is not None


AUTO_APPLY_CONFIDENCE = 92