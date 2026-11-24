import pytest

from app.config import Settings
from app.services.finance import freeagent_client
from app.services.finance.freeagent_adapter import _credentials_configured


def test_credentials_configured_requires_all_fields():
    assert not _credentials_configured(Settings())
    assert _credentials_configured(
        Settings(
            freeagent_client_id="id",
            freeagent_client_secret="secret",
            freeagent_redirect_uri="https://example.com/callback",
        )
    )


def test_authorization_url_includes_client_and_redirect():
    settings = Settings(
        freeagent_client_id="client-id",
        freeagent_redirect_uri="https://api.example.com/callback",
    )
    url = freeagent_client.authorization_url(settings, "state-xyz")
    assert "client-id" in url
    assert "state-xyz" in url
    assert "approve_app" in url


def test_authorization_url_missing_config_raises():
    with pytest.raises(ValueError):
        freeagent_client.authorization_url(Settings(), "state")


def test_token_expiry_from_payload():
    expiry = freeagent_client.token_expiry_from_payload({"expires_in": 3600})
    assert expiry is not None