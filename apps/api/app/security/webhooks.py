"""Fail-closed verification for inbound third-party webhooks."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException

_SIG_PREFIX = "sha256="


def verify_meta_signature(app_secret: str | None, body: bytes, header_value: str | None) -> None:
    """Reject unless X-Hub-Signature-256 is a valid HMAC-SHA256 of the raw body.

    An unset app secret rejects every request: we never accept unsigned Meta traffic.
    """
    if not app_secret:
        raise HTTPException(503, "Meta webhook not configured (META_APP_SECRET unset)")
    sig = (header_value or "").strip()
    if not sig.startswith(_SIG_PREFIX):
        raise HTTPException(403, "Missing or malformed signature")
    provided = sig[len(_SIG_PREFIX) :]
    if len(provided) != 64:
        raise HTTPException(403, "Missing or malformed signature")
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided.lower(), expected):
        raise HTTPException(403, "Invalid signature")


def verify_subscription_challenge(configured_token: str | None, mode: str, token: str, challenge: str) -> int:
    if not configured_token:
        raise HTTPException(503, "Webhook verify token not configured")
    if mode != "subscribe" or not hmac.compare_digest(token, configured_token):
        raise HTTPException(403, "Verification failed")
    try:
        return int(challenge)
    except ValueError as exc:
        raise HTTPException(400, "Invalid challenge") from exc


def verify_shared_secret(configured: str | None, provided: str | None, name: str) -> None:
    if not configured:
        raise HTTPException(503, f"{name} not configured")
    if not provided or not hmac.compare_digest(provided, configured):
        raise HTTPException(403, "Invalid webhook secret")
