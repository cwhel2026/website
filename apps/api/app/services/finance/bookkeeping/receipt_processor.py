"""Telegram receipt ingest — extraction via optional OpenAI vision; never fabricates totals."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.bookkeeping import BookkeepingReviewItem, ReviewItemStatus
from app.models.finance import BankTransaction, Expense, ExpenseCategory, Receipt, SyncSource
from app.services.finance.bookkeeping.categorizer import suggest_for_description
from app.services.finance.bookkeeping.review_queue import create_review_for_transaction
from app.services.finance.document_store import save_receipt_bytes
from app.services.telegram.client import TelegramApiError


@dataclass
class ReceiptExtraction:
    merchant: str | None
    transacted_at: date | None
    total_gbp: Decimal | None
    net_gbp: Decimal | None
    vat_gbp: Decimal | None
    vat_number: str | None
    payment_method: str | None
    line_items: list[str]
    confidence: str
    raw: dict[str, Any]


async def download_telegram_file(file_id: str) -> tuple[bytes, str]:
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        raise TelegramApiError("Telegram not configured")
    base = "https://api.telegram.org"
    async with httpx.AsyncClient(timeout=60) as client:
        meta = await client.get(f"{base}/bot{token}/getFile", params={"file_id": file_id})
        meta.raise_for_status()
        path = meta.json().get("result", {}).get("file_path")
        if not path:
            raise TelegramApiError("Telegram file path missing")
        file_res = await client.get(f"{base}/file/bot{token}/{path}")
        file_res.raise_for_status()
        name = path.rsplit("/", 1)[-1]
        return file_res.content, name


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        text = str(value).replace("£", "").replace(",", "").strip()
        amount = Decimal(text)
        return amount.quantize(Decimal("0.01")) if amount.is_finite() and amount >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


async def extract_receipt_fields(image_bytes: bytes, mime: str = "image/jpeg") -> ReceiptExtraction:
    settings = get_settings()
    if not settings.openai_api_key:
        return ReceiptExtraction(
            merchant=None,
            transacted_at=None,
            total_gbp=None,
            net_gbp=None,
            vat_gbp=None,
            vat_number=None,
            payment_method=None,
            line_items=[],
            confidence="manual_required",
            raw={"reason": "OPENAI_API_KEY not set — enter details in dashboard"},
        )

    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract UK receipt fields as JSON only. Keys: merchant, date (YYYY-MM-DD), "
                    "total_gbp, net_gbp, vat_gbp, vat_number, payment_method, line_items (array). "
                    "If unreadable, set confidence low in a field missing and do not invent numbers."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract this receipt:"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=90) as client:
        res = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
        )
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {"parse_error": content[:500]}

    return ReceiptExtraction(
        merchant=(data.get("merchant") or data.get("supplier")),
        transacted_at=_parse_date(data.get("date")),
        total_gbp=_parse_decimal(data.get("total_gbp")),
        net_gbp=_parse_decimal(data.get("net_gbp")),
        vat_gbp=_parse_decimal(data.get("vat_gbp")),
        vat_number=data.get("vat_number"),
        payment_method=data.get("payment_method"),
        line_items=list(data.get("line_items") or []),
        confidence="extracted" if data.get("total_gbp") else "low",
        raw=data,
    )


async def match_receipt_to_bank_transaction(
    db: AsyncSession,
    receipt: Receipt,
    tolerance_gbp: Decimal = Decimal("0.05"),
    day_window: int = 7,
) -> BankTransaction | None:
    total = receipt.extracted_total_gbp
    if total is None or not total.is_finite() or total <= 0 or receipt.extracted_date is None:
        return None
    target = -total
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.amount_gbp.between(target - tolerance_gbp, target + tolerance_gbp),
            BankTransaction.amount_gbp < 0,
            BankTransaction.transacted_at.between(receipt.extracted_date - timedelta(days=day_window), receipt.extracted_date + timedelta(days=day_window)),
            BankTransaction.is_duplicate.is_(False),
            ~BankTransaction.id.in_(select(Receipt.matched_bank_transaction_id).where(Receipt.matched_bank_transaction_id.is_not(None), Receipt.id != receipt.id)),
        ).order_by(BankTransaction.id).with_for_update()
    )
    candidates = list(result.scalars().all())
    # Amount and date alone are only a candidate, never proof of reconciliation.
    return candidates[0] if len(candidates) == 1 else None


async def ingest_telegram_receipt(
    db: AsyncSession,
    file_id: str,
    *,
    mime_hint: str = "image/jpeg",
) -> tuple[Receipt, str]:
    content, filename = await download_telegram_file(file_id)
    storage_key, digest = save_receipt_bytes(content, filename)

    await db.execute(text('SELECT pg_advisory_xact_lock(52703111)'))
    existing = await db.execute(select(Receipt).where(Receipt.content_sha256 == digest))
    dup = existing.scalar_one_or_none()
    if dup:
        return dup, "duplicate_receipt"

    extraction = await extract_receipt_fields(content, mime_hint)
    merchant = extraction.merchant or "Unknown merchant"

    receipt = Receipt(
        filename=filename,
        storage_key=storage_key,
        content_sha256=digest,
        telegram_file_id=file_id,
        extracted_merchant=merchant[:200],
        extracted_total_gbp=extraction.total_gbp,
        extracted_net_gbp=extraction.net_gbp,
        extracted_vat_gbp=extraction.vat_gbp,
        extracted_vat_number=extraction.vat_number,
        extracted_date=extraction.transacted_at,
        payment_method=extraction.payment_method,
        processing_status="extracted" if extraction.total_gbp else "needs_review",
        ocr_status=extraction.confidence,
        raw_extraction_json=json.dumps(extraction.raw)[:8000],
    )
    db.add(receipt)
    await db.flush()

    matched = await match_receipt_to_bank_transaction(db, receipt)
    summary: list[str] = []
    if matched:
        receipt.matched_bank_transaction_id = matched.id
        receipt.processing_status = "needs_review"
        if not matched.review_item_id:
            await create_review_for_transaction(db, matched)
        summary.append(f"Suggested bank match (review required): {matched.description[:60]} ({matched.transacted_at}).")
    elif extraction.total_gbp:
        receipt.processing_status = "needs_review"
        suggestion = suggest_for_description(merchant, -abs(extraction.total_gbp))
        item = BookkeepingReviewItem(
            receipt_id=receipt.id,
            suggested_category=suggestion.category,
            confidence_score=60,
            plain_explanation="Receipt saved but no bank transaction matched yet — reconcile when import catches up.",
            status=ReviewItemStatus.PENDING,
            receipt_required=False,
            vat_likely=bool(extraction.vat_gbp),
        )
        db.add(item)
        summary.append("Saved to pending reconciliation queue.")
    else:
        summary.append("Could not read totals — add details in Finance hub or resend a clearer photo.")

    if extraction.total_gbp:
        cat = suggest_for_description(merchant, -abs(extraction.total_gbp))
        summary.append(f"Suggested category: {cat.category.value} ({cat.confidence}% confidence).")
        if cat.vat_likely:
            summary.append("Likely VAT — keep receipt for records.")
    from app.services.finance.receipt_accounting import classify_receipt_route, push_receipt_to_freeagent

    txn = matched
    route = classify_receipt_route(receipt, txn)
    receipt.accounting_route = route.value
    summary.append(f"Accounting route: {route.value}.")
    summary.append("Review and approve accounting treatment in the dashboard before posting.")
    return receipt, " ".join(summary)


def summarise_receipt_reply(receipt: Receipt, detail: str) -> str:
    lines = [
        "Receipt received.",
        f"Supplier: {receipt.extracted_merchant or 'unknown'}",
    ]
    if receipt.extracted_total_gbp is not None:
        lines.append(f"Total: £{receipt.extracted_total_gbp}")
    if receipt.extracted_vat_gbp is not None:
        lines.append(f"VAT: £{receipt.extracted_vat_gbp}")
    if receipt.freeagent_attach_status:
        lines.append(f"FreeAgent: {receipt.freeagent_attach_status}")
    lines.append(detail)
    if receipt.ocr_status == "manual_required":
        lines.append("Tip: set OPENAI_API_KEY on the API service for automatic reading.")
    return "\n".join(lines)[:4096]