"""Attach receipt files to FreeAgent bank explanations when approved — never silent failure."""

from __future__ import annotations

import base64
import mimetypes
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.finance import BankTransaction, Receipt
from app.services.finance import freeagent_client
from app.services.finance.document_store import receipt_file_path
from app.services.finance.freeagent_adapter import ensure_fresh_token, get_connection_row


async def attach_receipt_to_freeagent(
    db: AsyncSession,
    receipt: Receipt,
    *,
    require_explanation_url: bool = True,
) -> dict:
    settings = get_settings()
    if not receipt.storage_key:
        return {"attached": False, "reason": "no_local_file"}
    if not receipt.matched_bank_transaction_id:
        return {"attached": False, "reason": "no_matched_transaction"}

    txn = await db.get(BankTransaction, receipt.matched_bank_transaction_id)
    if txn is None or not txn.freeagent_url:
        return {"attached": False, "reason": "bank_line_not_from_freeagent"}

    if require_explanation_url and not txn.freeagent_explanation_url:
        receipt.freeagent_attach_status = "needs_explanation_in_freeagent"
        receipt.freeagent_attach_error = (
            "Explain this bank transaction in FreeAgent first, then re-sync and approve attachment."
        )
        await db.flush()
        return {"attached": False, "reason": "missing_explanation_url"}

    row = await get_connection_row(db)
    if row is None:
        return {"attached": False, "reason": "not_connected"}

    try:
        token = await ensure_fresh_token(db, row, settings)
        content = receipt_file_path(receipt.storage_key).read_bytes()
    except OSError as exc:
        receipt.freeagent_attach_status = "file_missing"
        receipt.freeagent_attach_error = str(exc)
        await db.flush()
        return {"attached": False, "reason": "file_missing"}

    mime = mimetypes.guess_type(receipt.filename)[0] or "image/jpeg"
    b64 = base64.b64encode(content).decode("ascii")
    dated = receipt.extracted_date or txn.transacted_at or date.today()
    gross = receipt.extracted_total_gbp or abs(txn.amount_gbp)

    try:
        await freeagent_client.attach_explanation_receipt(
            settings,
            token,
            txn.freeagent_explanation_url or "",
            dated_on=dated.isoformat(),
            gross_value=str(gross),
            bank_transaction_url=txn.freeagent_url,
            file_name=receipt.filename[:200],
            content_type=mime,
            data_b64=b64,
            description=receipt.extracted_merchant or receipt.filename,
        )
        receipt.freeagent_attach_status = "attached"
        receipt.freeagent_attach_error = None
        txn.is_reconciled = True
        await db.flush()
        return {"attached": True, "freeagent_transaction": txn.freeagent_url}
    except Exception as exc:
        receipt.freeagent_attach_status = "failed"
        receipt.freeagent_attach_error = str(exc)[:500]
        await db.flush()
        return {"attached": False, "reason": "api_error", "detail": str(exc)[:200]}