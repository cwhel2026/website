"""UK Ltd onboarding checklist — plain-language tasks with deadline hints."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import (
    CompanyOnboardingTask,
    CompanyProfile,
    OnboardingTaskStatus,
    PayrollStatus,
    VatStatus,
)

DEFAULT_TASKS: list[dict] = [
    {
        "slug": "companies_house",
        "title": "Companies House registration",
        "plain_language": (
            "Register a private limited company at Companies House (or confirm your company number). "
            "You will receive a certificate of incorporation and must keep statutory records."
        ),
        "sort_order": 10,
    },
    {
        "slug": "identity_verification",
        "title": "Director identity verification",
        "plain_language": (
            "Directors may need to verify identity with Companies House under current rules. "
            "Check GOV.UK for whether this applies to you and complete before your filing deadlines."
        ),
        "sort_order": 20,
    },
    {
        "slug": "hmrc_corporation_tax",
        "title": "HMRC corporation tax registration",
        "plain_language": (
            "Tell HMRC within 3 months of starting to trade that the company exists and is active. "
            "You will get a company UTR (Unique Taxpayer Reference)."
        ),
        "sort_order": 30,
    },
    {
        "slug": "business_bank",
        "title": "Business bank account (e.g. Mettle)",
        "plain_language": (
            "Use a dedicated business bank account for all company income and expenses. "
            "Connect it to FreeAgent for bookkeeping — Mettle feeds into FreeAgent when linked."
        ),
        "sort_order": 40,
    },
    {
        "slug": "freeagent",
        "title": "FreeAgent bookkeeping",
        "plain_language": (
            "FreeAgent is the authoritative books system for this platform. "
            "Connect OAuth from the Finance dashboard — we sync invoices and bank data when APIs allow."
        ),
        "sort_order": 50,
    },
    {
        "slug": "paye",
        "title": "PAYE registration (if paying salary)",
        "plain_language": (
            "Register as an employer before the first payday if you pay yourself or staff through payroll. "
            "You must report through Real Time Information (RTI)."
        ),
        "sort_order": 60,
    },
    {
        "slug": "vat",
        "title": "VAT registration",
        "plain_language": (
            "You must register when taxable turnover exceeds the statutory threshold (monitor in the Tax centre). "
            "Do not register early without advice if turnover is below the threshold."
        ),
        "sort_order": 70,
    },
    {
        "slug": "statutory_records",
        "title": "Statutory company records",
        "plain_language": (
            "Keep register of members, directors, PSC information, minutes and resolutions. "
            "Store securely for at least the statutory retention period."
        ),
        "sort_order": 80,
    },
    {
        "slug": "insurance",
        "title": "Business insurance",
        "plain_language": (
            "Consider public liability and any trade-specific cover. "
            "Record renewal dates so policies do not lapse unnoticed."
        ),
        "sort_order": 90,
    },
    {
        "slug": "accountant_review",
        "title": "Professional accountant review",
        "plain_language": (
            "Have a qualified accountant review your company structure, remuneration strategy and first-year filings. "
            "AI guidance here is not a substitute for professional advice."
        ),
        "sort_order": 100,
    },
]


async def ensure_onboarding_tasks(db: AsyncSession) -> list[CompanyOnboardingTask]:
    existing = await db.execute(
        select(CompanyOnboardingTask).order_by(CompanyOnboardingTask.sort_order)
    )
    rows = list(existing.scalars().all())
    if rows:
        return rows
    created: list[CompanyOnboardingTask] = []
    for spec in DEFAULT_TASKS:
        task = CompanyOnboardingTask(
            slug=spec["slug"],
            title=spec["title"],
            plain_language=spec["plain_language"],
            sort_order=spec["sort_order"],
            status=OnboardingTaskStatus.INFO_REQUIRED,
        )
        db.add(task)
        created.append(task)
    await db.flush()
    return created


def _due_from_incorporation(inc: date | None, months: int) -> date | None:
    if inc is None:
        return None
    try:
        return inc + timedelta(days=months * 30)
    except Exception:
        return None


async def refresh_task_statuses(db: AsyncSession, profile: CompanyProfile) -> None:
    tasks = await ensure_onboarding_tasks(db)
    by_slug = {t.slug: t for t in tasks}

    if profile.companies_house_number:
        t = by_slug.get("companies_house")
        if t and t.status == OnboardingTaskStatus.INFO_REQUIRED:
            t.status = OnboardingTaskStatus.COMPLETED

    if profile.corporation_tax_registered:
        t = by_slug.get("hmrc_corporation_tax")
        if t:
            t.status = OnboardingTaskStatus.COMPLETED
    elif profile.trading_start_date:
        t = by_slug.get("hmrc_corporation_tax")
        if t:
            t.status = OnboardingTaskStatus.PREPARATION_REQUIRED
            t.due_date = _due_from_incorporation(profile.trading_start_date, 3)

    if profile.freeagent_configured:
        t = by_slug.get("freeagent")
        if t:
            t.status = OnboardingTaskStatus.COMPLETED

    if profile.vat_status == VatStatus.REGISTERED:
        t = by_slug.get("vat")
        if t:
            t.status = OnboardingTaskStatus.COMPLETED

    if profile.paye_status == PayrollStatus.REGISTERED:
        t = by_slug.get("paye")
        if t:
            t.status = OnboardingTaskStatus.COMPLETED

    await db.flush()


async def get_or_create_profile(db: AsyncSession) -> CompanyProfile:
    result = await db.execute(select(CompanyProfile).limit(1))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = CompanyProfile(registered_name="Revive My Drive Ltd")
        db.add(profile)
        await db.flush()
    await ensure_onboarding_tasks(db)
    await refresh_task_statuses(db, profile)
    return profile