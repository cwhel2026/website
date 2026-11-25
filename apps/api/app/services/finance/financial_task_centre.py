"""Actionable finance tasks for first-time ltd directors."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.company import CompanyOnboardingTask, OnboardingTaskStatus
from app.services.compliance.engine import upcoming_reminders
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.finance.watchdog import run_financial_watchdog


def _task(
    slug: str,
    title: str,
    why: str,
    when: str,
    how: str,
    *,
    professional: bool = False,
    severity: str = "normal",
    due: date | None = None,
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "why": why,
        "when": when,
        "how": how,
        "professional_assistance": professional,
        "severity": severity,
        "due_date": due.isoformat() if due else None,
    }


async def build_financial_tasks(db: AsyncSession, *, limit: int = 25) -> list[dict]:
    tasks: list[dict] = []

    for ob in await upcoming_reminders(db, within_days=60):
        tasks.append(
            _task(
                f"compliance_{ob['slug']}",
                ob["title"],
                ob.get("why_it_matters", "Statutory obligation for a UK limited company."),
                f"Due {ob['due_date']}" if ob.get("due_date") else "Check calendar",
                ob.get("plain_language", "Open Tax centre or ask accountant.")[:300],
                professional=True,
                severity="high" if ob.get("days_left", 99) <= 14 else "normal",
                due=date.fromisoformat(ob["due_date"]) if ob.get("due_date") else None,
            )
        )

    watchdog = await run_financial_watchdog(db)
    for issue in watchdog[:10]:
        tasks.append(
            _task(
                issue["code"],
                issue["title"],
                "Keeps HMRC and cash flow surprises away.",
                "As soon as practical",
                issue["detail"][:300],
                professional=issue["severity"] == "high",
                severity=issue["severity"],
            )
        )

    fa = await freeagent_status(db)
    if not fa.can_sync:
        tasks.append(
            _task(
                "connect_freeagent",
                "Connect FreeAgent",
                "Your books must match bank and VAT records.",
                "Before month-end",
                "Finance dashboard → Connect FreeAgent → full sync.",
                professional=False,
                severity="high",
            )
        )
    elif fa.last_sync_at is None:
        tasks.append(
            _task(
                "freeagent_sync",
                "Run FreeAgent sync",
                "Stale figures break tax reserves and director pay advice.",
                "Today",
                "Dashboard → Finance → Sync.",
                severity="medium",
            )
        )

    pending = await db.execute(
        select(BookkeepingReviewItem).where(BookkeepingReviewItem.status == ReviewItemStatus.PENDING).limit(15)
    )
    for item in pending.scalars().all():
        tasks.append(
            _task(
                f"review_{item.id}",
                "Review a bank transaction",
                "Wrong categories break tax and dividends.",
                "Within 7 days",
                item.plain_explanation[:240],
                professional=item.is_personal_expenditure,
                severity="normal",
            )
        )

    onboard = await db.execute(
        select(CompanyOnboardingTask).where(
            CompanyOnboardingTask.status.notin_(
                [OnboardingTaskStatus.COMPLETED, OnboardingTaskStatus.NOT_APPLICABLE]
            )
        )
    )
    for row in onboard.scalars().all():
        tasks.append(
            _task(
                row.slug,
                row.title,
                row.plain_language[:200],
                row.due_date.isoformat() if row.due_date else "See onboarding",
                "Company setup wizard in dashboard.",
                professional=True,
                due=row.due_date,
            )
        )

    tasks.sort(key=lambda t: (0 if t["severity"] == "high" else 1, t["due_date"] or "9999"))
    return tasks[:limit]


async def task_centre_plain_summary(db: AsyncSession) -> str:
    tasks = await build_financial_tasks(db, limit=8)
    if not tasks:
        return "No urgent finance tasks — keep photographing receipts in Telegram."
    lines = ["Your finance task list:"]
    for t in tasks:
        prof = " (ask accountant)" if t["professional_assistance"] else ""
        lines.append(f"• {t['title']}{prof} — {t['when']}")
    return "\n".join(lines)[:3500]