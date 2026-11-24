import pytest

from app.config import Settings
from app.security.startup import validate_production_settings


def test_production_rejects_weak_jwt():
    settings = Settings(
        environment="production",
        jwt_secret="dev-secret-change-in-production",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(settings)


def test_development_allows_default_jwt():
    settings = Settings(environment="development", jwt_secret="dev-secret-change-in-production")
    validate_production_settings(settings)


def test_production_accepts_strong_jwt():
    settings = Settings(
        environment="production",
        jwt_secret="x" * 40,
        default_admin_password="UniqueLocalPass-2026!",
    )
    validate_production_settings(settings)