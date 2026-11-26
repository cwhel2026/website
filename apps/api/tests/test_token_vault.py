import pytest

from app.config import get_settings
from app.services.finance import token_vault as vault

KEY = "unit-test-finance-key-at-least-32-chars"
JWT = "unit-test-jwt-secret-at-least-32-characters"


@pytest.fixture()
def configure(monkeypatch):
    def _set(key: str | None):
        monkeypatch.setenv("JWT_SECRET", JWT)
        if key is None:
            monkeypatch.delenv("FINANCE_TOKEN_ENCRYPTION_KEY", raising=False)
        else:
            monkeypatch.setenv("FINANCE_TOKEN_ENCRYPTION_KEY", key)
        get_settings.cache_clear()

    yield _set
    get_settings.cache_clear()


def test_encrypt_refuses_without_key(configure):
    configure(None)
    with pytest.raises(vault.TokenVaultError):
        vault.encrypt_token("secret")
    assert vault.encryption_configured() is False


def test_short_key_is_not_accepted(configure):
    configure("too-short")
    with pytest.raises(vault.TokenVaultError):
        vault.encrypt_token("secret")


def test_roundtrip_with_key(configure):
    configure(KEY)
    sealed = vault.encrypt_token("secret")
    assert sealed != "secret"
    assert vault.decrypt_token(sealed) == "secret"
    assert vault.needs_reencryption(sealed) is False


def test_legacy_jwt_ciphertext_is_read_and_reencrypted(configure):
    legacy = vault._derive(JWT).encrypt(b"old-token").decode()
    configure(KEY)
    assert vault.decrypt_token(legacy) == "old-token"
    assert vault.needs_reencryption(legacy) is True
    rotated = vault.reencrypt_if_legacy(legacy)
    assert rotated != legacy
    assert vault.needs_reencryption(rotated) is False
    assert vault.decrypt_token(rotated) == "old-token"


def test_legacy_plaintext_is_reencrypted(configure):
    configure(KEY)
    assert vault.decrypt_token("plain-token") == "plain-token"
    rotated = vault.reencrypt_if_legacy("plain-token")
    assert rotated != "plain-token"
    assert vault.decrypt_token(rotated) == "plain-token"


def test_undecryptable_ciphertext_is_an_error_not_returned(configure):
    foreign = vault._derive("some-other-key-that-is-long-enough!!").encrypt(b"x").decode()
    configure(KEY)
    with pytest.raises(vault.TokenVaultError):
        vault.decrypt_token(foreign)
