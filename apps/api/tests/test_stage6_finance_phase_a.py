from decimal import Decimal

from app.services.finance.token_vault import decrypt_token, encrypt_token
from app.services.tax_engine.corporation_tax import estimate_corporation_tax
from app.services.tax_engine.rules_uk_ltd import ACTIVE_RULES


def test_token_vault_roundtrip(monkeypatch):
    monkeypatch.setenv("FINANCE_TOKEN_ENCRYPTION_KEY", "test-finance-key-32chars-minimum!!")
    from app.config import get_settings

    get_settings.cache_clear()
    plain = "freeagent-access-token-example"
    sealed = encrypt_token(plain)
    assert sealed != plain
    assert decrypt_token(sealed) == plain


def test_corporation_tax_estimate_includes_rule_version():
    result = estimate_corporation_tax(Decimal("10000"), uses_small_profits_rate=True)
    assert result["estimated_corporation_tax_gbp"] == Decimal("1900.00") or float(
        result["estimated_corporation_tax_gbp"]
    ) == 1900.0
    assert result["rule_version"] == ACTIVE_RULES.version
    assert result["requires_accountant_review"] is True


def test_vat_threshold_constant():
    assert ACTIVE_RULES.vat_registration_threshold_gbp == Decimal("90000")