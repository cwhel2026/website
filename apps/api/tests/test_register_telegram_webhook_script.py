import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Import script module by path (not installed as package)
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR.parent))


def test_api_base_url_prefers_public_api_base_url(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com/")
    monkeypatch.delenv("RAILWAY_PUBLIC_DOMAIN", raising=False)
    from scripts.register_telegram_webhook import _api_base_url

    assert _api_base_url() == "https://api.example.com"


def test_api_base_url_railway_domain_fallback(monkeypatch):
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "my-api.up.railway.app")
    from scripts.register_telegram_webhook import _api_base_url

    assert _api_base_url() == "https://my-api.up.railway.app"


def test_webhook_path():
    from scripts.register_telegram_webhook import _webhook_path

    assert _webhook_path() == "/api/v1/telegram/webhook"


def test_mask_never_leaks_full_token():
    from scripts.register_telegram_webhook import _mask

    assert _mask("1234567890:ABCDEFghijklmnopqrstuvwxyz") == "1234…wxyz"
    assert "ABCDEF" not in _mask("1234567890:ABCDEFghijklmnopqrstuvwxyz")