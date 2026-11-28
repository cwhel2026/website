from decimal import Decimal
import hashlib
import hmac

import httpx
import pytest

from app.services.payments.gocardless import (
    GoCardlessClient, GoCardlessError, calculate_deposit, pounds_to_pence,
    payment_event_status, verify_webhook_signature,
)


def test_money_in_integer_pence_and_default_deposit():
    assert pounds_to_pence("850.00") == 85000
    assert calculate_deposit("850.00") == 8500
    assert calculate_deposit(Decimal("1200.00"), "12.5") == 15000
    assert calculate_deposit("0.05", "10") == 1
    with pytest.raises(ValueError):
        pounds_to_pence("1.001")
    with pytest.raises(ValueError):
        calculate_deposit("100", "0")
    with pytest.raises(ValueError):
        calculate_deposit("100", "Infinity")


def test_webhook_verification_checks_exact_raw_body():
    body = b'{"events":[{"id":"EV123"}]}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, signature, secret)
    assert not verify_webhook_signature(body + b" ", signature, secret)
    assert not verify_webhook_signature(body, None, secret)


def test_payment_events_do_not_assume_mandate_means_paid():
    assert payment_event_status("submitted") == "submitted"
    assert payment_event_status("confirmed") == "confirmed"
    assert payment_event_status("paid_out") == "paid_out"
    assert payment_event_status("failed") == "failed"
    assert payment_event_status("irrelevant") is None


@pytest.mark.asyncio
async def test_provider_uses_sandbox_idempotency_and_hosted_link():
    requests = []
    def handler(request: httpx.Request):
        requests.append(request)
        if request.url.path == "/billing_requests":
            return httpx.Response(201, json={"billing_requests": {"id": "BR123"}})
        return httpx.Response(201, json={"billing_request_flows": {"authorisation_url": "https://pay.gocardless.com/test"}})
    client = GoCardlessClient("sandbox-example", transport=httpx.MockTransport(handler))
    created = await client.create_billing_request(amount_pence=8500, reference="SC-001", idempotency_key="deposit:SC-001")
    assert created["billing_requests"]["id"] == "BR123"
    flow = await client.create_billing_request_flow(billing_request_id="BR123",
        redirect_uri="https://surfacecoat.co.uk/payment/return",
        exit_uri="https://surfacecoat.co.uk/payment/cancel", idempotency_key="flow:SC-001")
    assert flow["billing_request_flows"]["authorisation_url"].startswith("https://")
    assert requests[0].url.host == "api-sandbox.gocardless.com"
    assert requests[0].headers["Idempotency-Key"] == "deposit:SC-001"
    assert requests[1].url.path == "/billing_request_flows"
