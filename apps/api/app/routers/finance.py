from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin_writer, get_current_admin
from app.database import get_db
from app.models.finance import (
    BankTransaction,
    Expense,
    ExpenseCategory,
    Invoice,
    InvoiceStatus,
    Payment,
    Receipt,
    SyncSource,
)
from app.models.quotation import Quotation, QuotationStatus
from app.models.jobs import Job, JobStatus
from app.models.crm import Customer, Enquiry, PipelineStage
from app.models.user import User
from app.services.audit import record_audit
from app.services.finance.csv_import import import_bank_csv
from app.models.finance import FreeAgentConnectionState
from app.services.finance.freeagent_sync import sync_all_freeagent, sync_bank_transactions_from_freeagent
from app.services.finance.freeagent_adapter import (
    begin_oauth,
    complete_oauth,
    freeagent_status,
    sync_invoices_from_freeagent,
)
from app.services.finance.invoicing import create_invoice_from_quotation
from app.services.finance.profitability import job_profitability, territory_profitability
from app.services.tax_engine.corporation_tax import estimate_corporation_tax
from app.services.finance.tax_estimates import estimate_personal_tax

router = APIRouter(prefix="/finance", tags=["finance"])


class ExpenseIn(BaseModel):
    description: str
    category: ExpenseCategory
    amount_gbp: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    vat_gbp: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    job_id: UUID | None = None
    territory_id: UUID | None = None


class PaymentIn(BaseModel):
    amount_gbp: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: str = "bank_transfer"
    reference: str | None = None


@router.get("/status")
async def finance_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    fa = await freeagent_status(db)
    return {
        "freeagent": {
            "state": fa.state.value,
            "message": fa.message,
            "can_sync": fa.can_sync,
            "organisation_name": fa.organisation_name,
            "last_sync_at": fa.last_sync_at.isoformat() if fa.last_sync_at else None,
        },
        "mettle_feed": (
            "Bank feed via FreeAgent when connected — use CSV import until OAuth is complete."
            if fa.state != FreeAgentConnectionState.CONNECTED
            else "Mettle transactions sync through FreeAgent (not independently verified here)."
        ),
        "csv_import": True,
    }


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    user: Annotated[User, Depends(get_current_admin)] = ...,
) -> dict:
    content = (await file.read()).decode("utf-8", errors="replace")
    result = await import_bank_csv(db, content)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="finance.csv_import",
        detail={"imported": result.imported, "skipped": result.skipped_duplicates},
    )
    await db.commit()
    return {
        "imported": result.imported,
        "skipped_duplicates": result.skipped_duplicates,
        "errors": result.errors,
    }


@router.get("/invoices")
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(Invoice).order_by(Invoice.created_at.desc()).limit(100))
    return [
        {
            "id": str(i.id),
            "invoice_number": i.invoice_number,
            "status": i.status.value,
            "total_inc_vat_gbp": float(i.total_inc_vat_gbp),
            "amount_paid_gbp": float(i.amount_paid_gbp),
        }
        for i in result.scalars().all()
    ]


@router.post("/invoices/from-quotation/{quotation_id}")
async def invoice_from_quote(
    quotation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    q = await db.get(Quotation, quotation_id, with_for_update=True)
    if q is None:
        raise HTTPException(404, "Quotation not found")
    if q.is_test or q.status != QuotationStatus.ACCEPTED:
        raise HTTPException(409, "Accepted non-test quotation required")
    job = (await db.execute(select(Job).where(Job.quotation_id == q.id))).scalar_one_or_none()
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(409, "Complete the job before invoicing")
    existing = (await db.execute(select(Invoice).where(Invoice.quotation_id == q.id, Invoice.status != InvoiceStatus.VOID))).scalar_one_or_none()
    if existing:
        return {"invoice_number": existing.invoice_number, "id": str(existing.id)}
    inv = await create_invoice_from_quotation(db, q, q.customer_id, job_id=job.id)
    await record_audit(
        db, actor_type="user", actor_id=str(user.id), action="finance.create_invoice", entity_id=inv.id
    )
    await db.commit()
    return {"invoice_number": inv.invoice_number, "id": str(inv.id)}


@router.post("/invoices/{invoice_id}/payments")
async def record_payment(
    invoice_id: UUID,
    body: PaymentIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    inv = await db.get(Invoice, invoice_id, with_for_update=True)
    if inv is None:
        raise HTTPException(404)
    if inv.freeagent_id or inv.freeagent_url:
        raise HTTPException(409, "Record payment in FreeAgent and sync")
    if inv.status in (InvoiceStatus.VOID, InvoiceStatus.DRAFT):
        raise HTTPException(409, "Invoice must be issued before recording payment")
    if not body.reference or not body.reference.strip():
        raise HTTPException(422, "Payment reference required")
    body.reference = body.reference.strip()
    if body.reference.startswith('bank-match:'):
        raise HTTPException(422, 'Reserved payment reference')
    existing = (await db.execute(select(Payment).where(Payment.invoice_id == invoice_id, Payment.reference == body.reference))).scalar_one_or_none()
    if existing:
        if existing.amount_gbp != body.amount_gbp:
            raise HTTPException(409, "Payment reference already used with different amount")
        return {"status": inv.status.value, "amount_paid_gbp": float(inv.amount_paid_gbp)}
    if inv.amount_paid_gbp + body.amount_gbp > inv.total_inc_vat_gbp:
        raise HTTPException(422, "Payment exceeds outstanding balance")
    db.add(
        Payment(
            invoice_id=invoice_id,
            amount_gbp=body.amount_gbp,
            paid_at=datetime.now(UTC),
            method=body.method,
            reference=body.reference,
            source=SyncSource.MANUAL,
        )
    )
    inv.amount_paid_gbp += body.amount_gbp
    if inv.amount_paid_gbp >= inv.total_inc_vat_gbp:
        inv.status = InvoiceStatus.PAID
    elif inv.amount_paid_gbp > 0:
        inv.status = InvoiceStatus.PART_PAID
    if inv.status == InvoiceStatus.PAID and inv.quotation_id:
        q = await db.get(Quotation, inv.quotation_id)
        if q and q.enquiry_id:
            enquiry = await db.get(Enquiry, q.enquiry_id)
            if enquiry:
                enquiry.stage = PipelineStage.PAID
    await db.commit()
    return {"status": inv.status.value, "amount_paid_gbp": float(inv.amount_paid_gbp)}


@router.get("/expenses")
async def list_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(select(Expense).order_by(Expense.expense_date.desc()).limit(200))
    return [
        {
            "id": str(e.id),
            "description": e.description,
            "category": e.category.value,
            "amount_gbp": float(e.amount_gbp),
            "expense_date": e.expense_date.isoformat(),
        }
        for e in result.scalars().all()
    ]


@router.post("/expenses")
async def create_expense(
    body: ExpenseIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    from datetime import date

    if body.vat_gbp > body.amount_gbp:
        raise HTTPException(422, 'VAT cannot exceed gross expense')
    exp = Expense(
        description=body.description,
        category=body.category,
        amount_gbp=body.amount_gbp,
        vat_gbp=body.vat_gbp,
        expense_date=date.today(),
        job_id=body.job_id,
        territory_id=body.territory_id,
        source=SyncSource.MANUAL,
    )
    db.add(exp)
    await db.commit()
    return {"id": str(exp.id)}


@router.post("/receipts")
async def upload_receipt_metadata(
    filename: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    """Receipt file storage not connected — records metadata only."""
    r = Receipt(filename=filename, ocr_status="awaiting_storage_integration")
    db.add(r)
    await db.commit()
    return {"id": str(r.id), "note": "Object storage integration required for file upload"}


@router.get("/transactions")
async def list_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    result = await db.execute(
        select(BankTransaction).order_by(BankTransaction.transacted_at.desc()).limit(200)
    )
    return [
        {
            "description": t.description,
            "amount_gbp": float(t.amount_gbp),
            "date": t.transacted_at.isoformat(),
            "source": t.source.value,
        }
        for t in result.scalars().all()
    ]


@router.get("/tax-estimate")
async def tax_estimate(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    est = await estimate_personal_tax(db)
    return est.__dict__


@router.get("/profitability/territories")
async def profitability_territories(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[dict]:
    rows = await territory_profitability(db)
    return [r.__dict__ for r in rows]


@router.get("/profitability/jobs/{job_id}")
async def profitability_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    row = await job_profitability(db, job_id)
    if row is None:
        raise HTTPException(404)
    return row.__dict__


@router.get("/freeagent/authorize")
async def freeagent_authorize(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    try:
        payload = await begin_oauth(db)
        await record_audit(
            db,
            actor_type="user",
            actor_id=str(user.id),
            action="finance.freeagent.authorize_start",
        )
        await db.commit()
        return payload
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/freeagent/callback")
async def freeagent_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        result = await complete_oauth(db, code, state)
        await db.commit()
        return {"ok": True, **result}
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(400, str(exc)) from exc
    except httpx.HTTPError as exc:
        await db.rollback()
        raise HTTPException(502, "FreeAgent token exchange failed") from exc


@router.post("/freeagent/sync")
async def freeagent_sync(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await sync_invoices_from_freeagent(db)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="finance.freeagent.sync",
        detail={"synced": result.get("synced"), "fetched": result.get("fetched")},
    )
    await db.commit()
    return result


@router.post("/freeagent/sync/full")
async def freeagent_sync_full(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await sync_all_freeagent(db)
    await record_audit(
        db,
        actor_type="user",
        actor_id=str(user.id),
        action="finance.freeagent.sync_full",
        detail=result,
    )
    await db.commit()
    return result


@router.post("/freeagent/sync/bank")
async def freeagent_sync_bank(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin)],
) -> dict:
    result = await sync_bank_transactions_from_freeagent(db)
    await db.commit()
    return result


@router.get("/tax/corporation-estimate")
async def corporation_tax_estimate(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    profit_gbp: float = 0,
    small_profits_rate: bool = False,
) -> dict:
    from decimal import Decimal

    estimate = estimate_corporation_tax(Decimal(str(profit_gbp)), uses_small_profits_rate=small_profits_rate)
    return estimate

class ConfirmBankPaymentIn(BaseModel):
    invoice_id: UUID
    confirmed: bool = False


@router.post("/transactions/{transaction_id}/confirm-payment")
async def confirm_bank_payment(
    transaction_id: UUID,
    body: ConfirmBankPaymentIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_admin_writer)],
) -> dict:
    if not body.confirmed:
        raise HTTPException(422, "Explicit payment confirmation required")
    txn = await db.get(BankTransaction, transaction_id, with_for_update=True)
    if txn is None:
        raise HTTPException(404, "Bank transaction not found")
    inv = await db.get(Invoice, body.invoice_id, with_for_update=True)
    if inv is None:
        raise HTTPException(404, "Invoice not found")
    reference = f"bank-match:{txn.id}"
    existing = (await db.execute(select(Payment).where(Payment.reference == reference))).scalar_one_or_none()
    if existing:
        if existing.invoice_id == inv.id and existing.amount_gbp == txn.amount_gbp and txn.matched_invoice_id == inv.id:
            return {"status": inv.status.value, "already_recorded": True}
        raise HTTPException(409, "Conflicting payment record")
    if txn.source == SyncSource.FREEAGENT or txn.freeagent_explanation_url or inv.freeagent_id or inv.freeagent_url:
        raise HTTPException(409, "Reconcile FreeAgent records in FreeAgent and sync")
    if txn.is_duplicate or txn.is_reconciled or txn.matched_invoice_id or txn.matched_expense_id or txn.amount_gbp <= 0:
        raise HTTPException(409, "Transaction is not eligible")
    customer = await db.get(Customer, inv.customer_id)
    quote = await db.get(Quotation, inv.quotation_id) if inv.quotation_id else None
    if not customer or customer.is_test or (quote and quote.is_test):
        raise HTTPException(409, "Non-test customer invoice required")
    if inv.status not in (InvoiceStatus.SENT, InvoiceStatus.PART_PAID, InvoiceStatus.OVERDUE):
        raise HTTPException(409, "Outstanding issued invoice required")
    if txn.transacted_at < inv.issue_date or txn.transacted_at > datetime.now(UTC).date():
        raise HTTPException(409, "Transaction date is outside eligible range")
    if txn.amount_gbp != inv.total_inc_vat_gbp - inv.amount_paid_gbp:
        raise HTTPException(409, "Payment must equal the outstanding balance")
    db.add(Payment(invoice_id=inv.id, amount_gbp=txn.amount_gbp,
        paid_at=datetime.combine(txn.transacted_at, time.min, tzinfo=UTC),
        method="bank_transfer", reference=reference, source=txn.source))
    inv.amount_paid_gbp += txn.amount_gbp
    inv.status = InvoiceStatus.PAID
    txn.matched_invoice_id = inv.id
    txn.is_reconciled = True
    if quote and quote.enquiry_id:
        enquiry = await db.get(Enquiry, quote.enquiry_id)
        if enquiry and not enquiry.is_test:
            enquiry.stage = PipelineStage.PAID
    await record_audit(db, actor_type="user", actor_id=str(user.id),
        action="finance.confirm_bank_payment", entity_id=inv.id,
        detail={"transaction_id": str(txn.id), "amount_gbp": str(txn.amount_gbp)})
    await db.commit()
    return {"status": inv.status.value, "already_recorded": False}
