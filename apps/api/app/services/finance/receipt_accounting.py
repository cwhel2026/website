"""Route receipts to the correct FreeAgent workflow — approval-gated writes."""

from __future__ import annotations

import base64
import json
import mimetypes
from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.finance import BankTransaction, Expense, Receipt
from app.models.freeagent_cache import FreeAgentResourceCache
from app.services.finance import freeagent_client
from app.services.finance.document_store import receipt_file_path
from app.services.finance.freeagent_adapter import ensure_fresh_token, freeagent_status, get_connection_row
from app.services.finance.freeagent_categories import resolve_category_url
from app.services.finance.freeagent_receipt_attach import attach_receipt_to_freeagent
from app.services.finance.bookkeeping.categorizer import suggest_for_description


class AccountingRoute(str, Enum):
    ALREADY_RECONCILED = "already_reconciled"
    COMPANY_BANK = "company_bank"
    PERSONAL_DIRECTOR = "personal_director"
    SUPPLIER_BILL = "supplier_bill"
    UNMATCHED = "unmatched"


PERSONAL_KEYWORDS = ("personal", "cash", "own card", "director paid", "reimburse")


def classify_receipt_route(
    receipt: Receipt,
    txn: BankTransaction | None,
) -> AccountingRoute:
    if txn and txn.is_reconciled:
        return AccountingRoute.ALREADY_RECONCILED
    method = (receipt.payment_method or "").lower()
    if txn and txn.amount_gbp < 0 and not txn.is_reconciled:
        receipt.accounting_route = AccountingRoute.COMPANY_BANK.value
        return AccountingRoute.COMPANY_BANK
    if any(k in method for k in PERSONAL_KEYWORDS):
        return AccountingRoute.PERSONAL_DIRECTOR
    if txn is None and receipt.extracted_total_gbp:
        return AccountingRoute.UNMATCHED
    if txn is None:
        merchant = (receipt.extracted_merchant or "").lower()
        if any(w in merchant for w in ("utilities", "supplier", "wholesale", "b&q", "travis")):
            return AccountingRoute.SUPPLIER_BILL
        return AccountingRoute.UNMATCHED
    return AccountingRoute.UNMATCHED


async def _duplicate_in_cache(db: AsyncSession, receipt: Receipt) -> bool:
    if receipt.extracted_total_gbp is None or receipt.extracted_date is None:
        return False
    result = await db.execute(
        select(FreeAgentResourceCache).where(FreeAgentResourceCache.resource_key == "expenses_cache")
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    payload = json.loads(row.payload_json)
    total = str(receipt.extracted_total_gbp)
    d = receipt.extracted_date.isoformat()
    for exp in payload.get("expenses") or []:
        if str(exp.get("dated_on", ""))[:10] == d and str(exp.get("gross_value")) == total:
            return True
    return False


async def push_receipt_to_freeagent(
    db: AsyncSession,
    receipt: Receipt,
    *,
    approved: bool,
) -> dict:
    if not approved:
        return {"ok": False, "reason": "approval_required"}
    await db.refresh(receipt, with_for_update=True)
    if receipt.freeagent_expense_url:
        return {"ok": True, "reason": "already_posted", "url": receipt.freeagent_expense_url}

    if receipt.freeagent_attach_status in ("posting", "failed", "uncertain"):
        return {"ok": False, "reason": "manual_verification_required"}
    if not receipt.extracted_date or receipt.extracted_total_gbp is None or not receipt.extracted_total_gbp.is_finite() or receipt.extracted_total_gbp <= 0:
        return {"ok": False, "reason": "verified_receipt_amount_and_date_required"}
    if receipt.extracted_vat_gbp is not None and (not receipt.extracted_vat_gbp.is_finite() or not 0 <= receipt.extracted_vat_gbp <= receipt.extracted_total_gbp):
        return {"ok": False, "reason": "invalid_receipt_vat"}
    settings = get_settings()
    status = await freeagent_status(db)
    if not status.can_sync:
        return {"ok": False, "reason": "freeagent_not_connected"}

    txn = None
    if receipt.matched_bank_transaction_id:
        txn = await db.get(BankTransaction, receipt.matched_bank_transaction_id)

    if txn and (txn.is_duplicate or receipt.processing_status == 'needs_review'):
        return {"ok": False, "reason": "verify_bank_match_first"}
    route = classify_receipt_route(receipt, txn)
    receipt.accounting_route = route.value
    await db.flush()

    if route == AccountingRoute.ALREADY_RECONCILED:
        return {"ok": False, "reason": "already_reconciled"}
    if route == AccountingRoute.SUPPLIER_BILL:
        return {
            "ok": False,
            "reason": "supplier_bill",
            "message": "Enter supplier bill in FreeAgent — API bill create not enabled.",
        }
    if await _duplicate_in_cache(db, receipt):
        receipt.processing_status = "duplicate_suspected"
        await db.flush()
        return {"ok": False, "reason": "duplicate_in_freeagent_cache"}

    local_dup = await db.execute(
        select(Expense).where(
            Expense.receipt_id == receipt.id,
        )
    )
    if local_dup.scalar_one_or_none() and receipt.freeagent_attach_status == "attached":
        return {"ok": True, "reason": "local_expense_exists"}

    if route == AccountingRoute.COMPANY_BANK:
        if settings.finance_receipt_freeagent_attach:
            return await attach_receipt_to_freeagent(db, receipt)
        return {"ok": False, "reason": "enable_FINANCE_RECEIPT_FREEAGENT_ATTACH"}

    if route == AccountingRoute.PERSONAL_DIRECTOR:
        if not settings.finance_receipt_freeagent_expense:
            return {
                "ok": False,
                "reason": "personal_expense_queued",
                "message": "Approve in dashboard; set FINANCE_RECEIPT_FREEAGENT_EXPENSE=true to post.",
            }
        row = await get_connection_row(db)
        if row is None:
            return {"ok": False, "reason": "not_connected"}
        try:
            token = await ensure_fresh_token(db, row, settings)
            me = await freeagent_client.fetch_users_me(settings, token)
            user_url = (me.get("user") or {}).get("url")
            if not user_url:
                return {"ok": False, "reason": "freeagent_user_url_missing"}
            amount = receipt.extracted_total_gbp or Decimal("0")
            cat = suggest_for_description(receipt.extracted_merchant or "", -abs(amount))
            category_url = await resolve_category_url(db, cat.category)
            if not category_url:
                return {"ok": False, "reason": "no_freeagent_category", "message": "Run full sync or set FA category URL."}
            content = receipt_file_path(receipt.storage_key or "").read_bytes()
            mime = mimetypes.guess_type(receipt.filename)[0] or "image/jpeg"
            b64 = base64.b64encode(content).decode("ascii")
            dated = receipt.extracted_date
            vat = receipt.extracted_vat_gbp or Decimal("0")
            receipt.freeagent_attach_status = 'posting'
            await db.flush()
            resp = await freeagent_client.create_expense_with_attachment(
                settings,
                token,
                user_url=user_url,
                category_url=category_url,
                dated_on=dated.isoformat(),
                description=(receipt.extracted_merchant or receipt.filename)[:255],
                gross_value=str(amount),
                sales_tax_value=str(vat),
                file_name=receipt.filename[:200],
                content_type=mime,
                data_b64=b64,
            )
            expense = resp.get("expense") or {}
            url = expense.get("url")
            if not url:
                receipt.freeagent_attach_status = "uncertain"
                await db.flush()
                return {"ok": False, "reason": "manual_verification_required"}
            receipt.freeagent_expense_url = str(url)[:255]
            receipt.freeagent_attach_status = "expense_created"
            receipt.processing_status = "posted_freeagent"
            await db.flush()
            return {"ok": True, "route": route.value, "freeagent_expense_url": receipt.freeagent_expense_url}
        except Exception as exc:
            receipt.freeagent_attach_status = "failed"
            receipt.freeagent_attach_error = type(exc).__name__
            await db.flush()
            return {"ok": False, "reason": "api_error", "detail": "Verify FreeAgent before retrying"}

    return {"ok": False, "reason": "unmatched", "route": route.value}