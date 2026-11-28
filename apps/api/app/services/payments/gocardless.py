"""GoCardless Direct Debit integration primitives.

No live charge is created by this module without an explicit caller action.
Never log request payloads or authorization tokens.
"""
from __future__ import annotations

import hashlib
import hmac
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx

SANDBOX_API = "https://api-sandbox.gocardless.com"
LIVE_API = "https://api.gocardless.com"
API_VERSION = "2015-07-06"


class GoCardlessError(Exception):
    """A provider operation failed. Details intentionally omit customer data."""


def pounds_to_pence(value: Decimal | str) -> int:
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise ValueError("Amount must be nonnegative to two decimal places")
    return int(amount * 100)


def calculate_deposit(total: Decimal | str, percentage: Decimal | str = "10") -> int:
    amount = pounds_to_pence(total)
    rate = Decimal(str(percentage))
    if not rate.is_finite() or not Decimal("0") < rate <= Decimal("100"):
        raise ValueError("Deposit percentage must be between 0 and 100")
    return int((Decimal(amount) * rate / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def verify_webhook_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature.strip())


PAYMENT_STATUS_EVENTS: dict[str, str] = {
    "created": "pending_submission",
    "customer_approval_granted": "pending_submission",
    "customer_approval_denied": "cancelled",
    "submitted": "submitted",
    "confirmed": "confirmed",
    "paid_out": "paid_out",
    "failed": "failed",
    "cancelled": "cancelled",
    "charged_back": "charged_back",
    "chargeback_cancelled": "confirmed",
}


def payment_event_status(action: str) -> str | None:
    return PAYMENT_STATUS_EVENTS.get(action)


class GoCardlessClient:
    def __init__(self, access_token: str, *, sandbox: bool = True, transport: httpx.AsyncBaseTransport | None = None):
        if not access_token:
            raise ValueError("A GoCardless API access token is required")
        self._token = access_token
        self._base = SANDBOX_API if sandbox else LIVE_API
        self._transport = transport

    async def _post(self, path: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        if not idempotency_key:
            raise ValueError("Idempotency key is required")
        headers = {
            "Authorization": f"Bearer {self._token}",
            "GoCardless-Version": API_VERSION,
            "Idempotency-Key": idempotency_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(base_url=self._base, headers=headers, timeout=20, transport=self._transport) as client:
                response = await client.post(path, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GoCardlessError("GoCardless request failed; inspect secure provider diagnostics") from exc

    async def create_billing_request(self, *, amount_pence: int, reference: str, idempotency_key: str) -> dict[str, Any]:
        if amount_pence < 1 or not reference:
            raise ValueError("Positive amount and booking reference required")
        return await self._post(
            "/billing_requests",
            {"billing_requests": {"payment_request": {"description": f"SurfaceCoat booking deposit {reference}",
                "amount": str(amount_pence), "currency": "GBP"}, "mandate_request": {"currency": "GBP", "scheme": "bacs"}}},
            idempotency_key,
        )

    async def create_billing_request_flow(self, *, billing_request_id: str, redirect_uri: str,
                                          exit_uri: str, idempotency_key: str) -> dict[str, Any]:
        if not billing_request_id or not redirect_uri.startswith("https://") or not exit_uri.startswith("https://"):
            raise ValueError("Valid billing request and HTTPS redirect URLs required")
        return await self._post("/billing_request_flows", {
            "billing_request_flows": {
                "links": {"billing_request": billing_request_id},
                "redirect_uri": redirect_uri,
                "exit_uri": exit_uri,
            }}, idempotency_key)
