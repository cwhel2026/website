"""Encrypt integration tokens at rest (Fernet) with FINANCE_TOKEN_ENCRYPTION_KEY.

Fail closed: without a key of at least 32 characters nothing is encrypted or
stored, and an undecryptable ciphertext is an error, never returned as-is.

Legacy values are still readable so existing connections keep working:
* ciphertext produced by the old JWT_SECRET-derived key,
* plaintext written when no key material existed.
Both are reported by ``needs_reencryption`` and rewritten under the current key
by ``reencrypt_if_legacy``.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

MIN_KEY_LENGTH = 32
_FERNET_PREFIX = "gAAAAA"


class TokenVaultError(RuntimeError):
    pass


def _derive(material: str) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(material.encode()).digest()))


def _primary() -> Fernet | None:
    key = (get_settings().finance_token_encryption_key or "").strip()
    if len(key) < MIN_KEY_LENGTH:
        return None
    return _derive(key)


def _legacy() -> Fernet | None:
    material = (get_settings().jwt_secret or "").strip()
    return _derive(material) if len(material) >= 16 else None


def encryption_configured() -> bool:
    return _primary() is not None


def encrypt_token(plaintext: str | None) -> str | None:
    if not plaintext:
        return None
    primary = _primary()
    if primary is None:
        raise TokenVaultError(
            "FINANCE_TOKEN_ENCRYPTION_KEY (at least 32 characters) is required to store integration tokens."
        )
    return primary.encrypt(plaintext.encode("utf-8")).decode("ascii")


def _decrypt(ciphertext: str) -> tuple[str, bool]:
    """Return (plaintext, is_legacy)."""
    primary = _primary()
    if primary is not None:
        try:
            return primary.decrypt(ciphertext.encode("ascii")).decode("utf-8"), False
        except (InvalidToken, UnicodeEncodeError):
            pass
    legacy = _legacy()
    if legacy is not None:
        try:
            return legacy.decrypt(ciphertext.encode("ascii")).decode("utf-8"), True
        except (InvalidToken, UnicodeEncodeError):
            pass
    if ciphertext.startswith(_FERNET_PREFIX):
        raise TokenVaultError("Stored token cannot be decrypted with the configured key.")
    return ciphertext, True


def decrypt_token(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return None
    return _decrypt(ciphertext)[0]


def needs_reencryption(ciphertext: str | None) -> bool:
    if not ciphertext:
        return False
    try:
        return _decrypt(ciphertext)[1]
    except TokenVaultError:
        return False


def reencrypt_if_legacy(ciphertext: str | None) -> str | None:
    """Rewrite a legacy value under the current key; unchanged when not possible or not needed."""
    if not ciphertext or not encryption_configured() or not needs_reencryption(ciphertext):
        return ciphertext
    return encrypt_token(decrypt_token(ciphertext))
