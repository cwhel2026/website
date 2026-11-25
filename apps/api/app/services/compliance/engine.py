"""Statutory compliance calendar — deadlines from company facts, not assumptions."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile, PayrollStatus, VatStatus
from app.models.compliance import ComplianceObligation, ComplianceStatus


def _accounts_due(inc: date, ref_month: int, ref_day: int) -> date:
    """Companies House accounts due 9 months after ARD."""
    try:
        ard = date(inc.year if inc.month <= ref_month else inc.year + 1, ref_month, ref_day)
    except ValueError:
        ard = date(inc.year, ref_month, min(ref_day, 28))
    return ard + timedelta(days=9 * 30)


def _confirmation_statement_due(inc: date) -> date:
    return inc + timedelta(days=365)


async def refresh_compliance_calendar(db: AsyncSession) -> list[ComplianceObligation]:
    profile = await db.execute(select(CompanyProfile).limit(1))
    prof = profile.scalar_one_or_none()

    templates: list[dict] = [
        {
            "slug": "confirmation_statement",
            "title": "Confirmation statement (Companies House)",
            "plain_language": (
                "Confirm your company details with Companies House at least once every 12 months."
            ),
            "why_it_matters": "Late filing can lead to penalties and strike-off risk.",
            "source_url": "https://www.gov.uk/government/organisations/companies-house",
            "sort_order": 10,
        },
        {
            "slug": "annual_accounts",
            "title": "Annual accounts filing",
            "plain_language": "File statutory accounts with Companies House after each financial year.",
            "why_it_matters": "Overdue accounts are published as overdue on the public register.",
            "source_url": "https://www.gov.uk/annual-accounts",
            "sort_order": 20,
        },
        {
            "slug": "corporation_tax_return",
            "title": "Corporation tax return (CT600)",
            "plain_language": (
                "Tell HMRC your company profits and pay corporation tax — usually within 12 months of your accounting period end."
            ),
            "why_it_matters": "Penalties accrue for late returns and late payment.",
            "source_url": "https://www.gov.uk/corporation-tax",
            "sort_order": 30,
        },
        {
            "slug": "personal_sa",
            "title": "Director Self Assessment",
            "plain_language": (
                "If HMRC requires a personal tax return (salary, dividends, other income), file and pay by 31 January."
            ),
            "why_it_matters": "Missed Self Assessment deadlines carry automatic penalties.",
            "source_url": "https://www.gov.uk/self-assessment-tax-returns",
            "sort_order": 40,
        },
    ]

    if prof and prof.vat_status == VatStatus.REGISTERED:
        templates.append(
            {
                "slug": "vat_return",
                "title": "VAT return and payment",
                "plain_language": "Submit your VAT return and pay VAT due for each VAT period.",
                "why_it_matters": "Late VAT attracts surcharges and interest.",
                "source_url": "https://www.gov.uk/how-to-pay-vat",
                "sort_order": 50,
            }
        )

    if prof and prof.paye_status == PayrollStatus.REGISTERED:
        templates.append(
            {
                "slug": "paye_rti",
                "title": "PAYE / RTI payroll submissions",
                "plain_language": "Report payroll to HMRC on or before each payday through RTI.",
                "why_it_matters": "Late RTI can stop EPS submissions and trigger penalties.",
                "source_url": "https://www.gov.uk/running-payroll",
                "sort_order": 60,
            }
        )

    existing = await db.execute(select(ComplianceObligation))
    by_slug = {o.slug: o for o in existing.scalars().all()}
    today = date.today()
    out: list[ComplianceObligation] = []

    for spec in templates:
        ob = by_slug.get(spec["slug"])
        if ob is None:
            ob = ComplianceObligation(
                slug=spec["slug"],
                title=spec["title"],
                plain_language=spec["plain_language"],
                why_it_matters=spec["why_it_matters"],
                source_url=spec["source_url"],
                sort_order=spec["sort_order"],
                status=ComplianceStatus.INFO_REQUIRED,
            )
            db.add(ob)
        else:
            ob.title = spec["title"]
            ob.plain_language = spec["plain_language"]
            ob.why_it_matters = spec["why_it_matters"]
            ob.source_url = spec["source_url"]

        due: date | None = None
        if prof and prof.incorporation_date:
            if spec["slug"] == "confirmation_statement":
                due = _confirmation_statement_due(prof.incorporation_date)
            elif spec["slug"] == "annual_accounts" and prof.accounting_reference_month:
                due = _accounts_due(
                    prof.incorporation_date,
                    prof.accounting_reference_month,
                    prof.accounting_reference_day or 28,
                )
            elif spec["slug"] == "corporation_tax_return" and prof.accounting_reference_month:
                due = _accounts_due(
                    prof.incorporation_date,
                    prof.accounting_reference_month,
                    prof.accounting_reference_day or 28,
                ) + timedelta(days=30)

        ob.due_date = due
        if due is None:
            ob.status = ComplianceStatus.INFO_REQUIRED
        elif due < today:
            ob.status = ComplianceStatus.OVERDUE
        elif (due - today).days <= 30:
            ob.status = ComplianceStatus.PREPARATION_REQUIRED
        else:
            ob.status = ComplianceStatus.UPCOMING
        out.append(ob)

    await db.flush()
    return out


async def upcoming_reminders(db: AsyncSession, within_days: int = 90) -> list[dict]:
    obligations = await refresh_compliance_calendar(db)
    today = date.today()
    horizon = today + timedelta(days=within_days)
    rows: list[dict] = []
    for ob in sorted(obligations, key=lambda x: (x.due_date or date.max, x.sort_order)):
        if ob.due_date and ob.due_date <= horizon:
            days_left = (ob.due_date - today).days
            rows.append(
                {
                    "slug": ob.slug,
                    "title": ob.title,
                    "due_date": ob.due_date.isoformat(),
                    "days_left": days_left,
                    "status": ob.status.value,
                    "plain_language": ob.plain_language,
                    "why_it_matters": ob.why_it_matters,
                    "source_url": ob.source_url,
                }
            )
    return rows