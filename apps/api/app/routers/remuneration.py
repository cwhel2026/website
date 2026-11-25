from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.remuneration import DividendProposal, DividendProposalStatus
from app.models.user import User
from app.services.audit import record_audit
from app.services.finance.distributable_reserves import compute_distributable_reserves
from app.services.finance.tax_reserves import compute_tax_reserves
from app.services.remuneration.directors_loan import loan_balance, sync_directors_loan_from_reviews
from app.services.remuneration.optimizer import RemunerationInputs, optimise_remuneration

router = APIRouter(prefix="/finance/remuneration", tags=["remuneration"])


class OptimiseIn(BaseModel):
    desired_monthly_net_gbp: Decimal = Field(gt=0)
    other_personal_income_gbp: Decimal = Decimal("0")
    annual_company_profit_gbp: Decimal | None = None
    distributable_reserves_gbp: Decimal | None = None
    company_cash_gbp: Decimal | None = None


@router.post("/optimise")
async def optimise_pay(
    body: OptimiseIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    reserves_payload = await compute_tax_reserves(db)
    dist = await compute_distributable_reserves(db)
    profit = body.annual_company_profit_gbp or Decimal(str(reserves_payload.get("profit_estimate_gbp", 0)))

    if not dist.get("available"):
        return {
            "blocked": True,
            "blocked_reason": dist.get("message", "FreeAgent reserves not available."),
            "requires_accountant_review": True,
            "distributable_reserves": dist,
        }

    reserves = body.distributable_reserves_gbp or Decimal(
        str(dist.get("after_tax_and_pending_dividends_gbp") or dist.get("distributable_profit_gbp") or 0)
    )
    cash = body.company_cash_gbp or reserves

    block_reasons: list[str] = []
    if dist.get("blocked"):
        block_reasons.append(dist.get("message") or "P&L vs balance sheet mismatch or provisional data.")
    if reserves_payload.get("is_provisional"):
        block_reasons.append("Accounting data provisional.")
    if reserves <= 0 and profit <= 0:
        block_reasons.append("No verified profit or reserves.")

    out = optimise_remuneration(
        RemunerationInputs(
            desired_monthly_net_gbp=body.desired_monthly_net_gbp,
            annual_company_profit_before_remuneration_gbp=profit,
            distributable_reserves_gbp=reserves,
            company_cash_gbp=cash,
            other_personal_income_gbp=body.other_personal_income_gbp,
        )
    )
    out["distributable_reserves"] = dist
    out["company_cash_gbp"] = float(cash)
    out["requires_accountant_review"] = True
    if block_reasons:
        out["blocked"] = True
        out["blocked_reason"] = " ".join(block_reasons)
    return out


class DividendProposalIn(BaseModel):
    amount_gbp: Decimal = Field(gt=0)
    proposed_payment_date: date
    distributable_profit_gbp: Decimal
    company_cash_gbp: Decimal


@router.post("/dividends/propose")
async def propose_dividend(
    body: DividendProposalIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    lawful = body.amount_gbp <= body.distributable_profit_gbp
    if body.amount_gbp > body.company_cash_gbp:
        lawful = False
    proposal = DividendProposal(
        amount_gbp=body.amount_gbp,
        proposed_payment_date=body.proposed_payment_date,
        distributable_profit_at_proposal_gbp=body.distributable_profit_gbp,
        company_cash_at_proposal_gbp=body.company_cash_gbp,
        lawful=lawful,
        status=DividendProposalStatus.AWAITING_APPROVAL,
        voucher_text=f"Dividend voucher draft — £{body.amount_gbp} (not paid until approved).",
        board_minutes_text="Board minutes draft — director declares interim dividend subject to profit.",
    )
    db.add(proposal)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="dividend.propose",
        entity_id=proposal.id,
    )
    await db.commit()
    return {
        "id": str(proposal.id),
        "lawful": lawful,
        "status": proposal.status.value,
        "requires_approval": True,
        "message": (
            "Lawful based on profit and cash figures supplied — still needs accountant sign-off."
            if lawful
            else "Not lawful — dividend exceeds distributable profit or cash. Do not pay."
        ),
    }


@router.post("/dividends/{proposal_id}/approve")
async def approve_dividend(
    proposal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    proposal = await db.get(DividendProposal, proposal_id)
    if proposal is None:
        raise HTTPException(404, "Proposal not found")
    if not proposal.lawful:
        raise HTTPException(400, "Cannot approve unlawful dividend proposal")
    from datetime import UTC, datetime

    proposal.status = DividendProposalStatus.APPROVED
    proposal.approved_at = datetime.now(UTC)
    await record_audit(db, actor_type="user", actor_id=str(user.id), action="dividend.approve", entity_id=proposal.id)
    await db.commit()
    return {"status": proposal.status.value, "note": "Approved in system only — no bank payment initiated."}


@router.get("/directors-loan")
async def directors_loan(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    await sync_directors_loan_from_reviews(db)
    bal = await loan_balance(db)
    await db.commit()
    return bal