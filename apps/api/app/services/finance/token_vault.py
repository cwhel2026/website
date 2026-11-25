"""Encrypt integration tokens at rest using a key derived from FINANCE_TOKEN_KEY or JWT_SECRET."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet | None:
    settings = get_settings()
    material = (settings.finance_token_encryption_key or settings.jwt_secret or "").encode()
    if len(material) < 16:
        return None
    digest = hashlib.sha256(material).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_token(plaintext: str | None) -> str | None:
    if not plaintext:
        return None
    f = _fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_token(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return None
    f = _fernet()
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ciphertext