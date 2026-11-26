from app.config import Settings

_INSECURE_JWT_DEFAULTS = frozenset(
    {
        "dev-secret-change-in-production",
        "change-me-in-production-use-long-random-string",
    }
)


def validate_production_settings(settings: Settings) -> None:
    if settings.environment.lower() != "production":
        return
    secret = settings.jwt_secret.strip()
    if secret in _INSECURE_JWT_DEFAULTS or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be a unique random string of at least 32 characters in production."
        )
    if settings.default_admin_password in (
        "ChangeMe-RMD-2025!",
        "change-on-first-login",
    ):
        import logging

        logging.getLogger(__name__).critical(
            "DEFAULT_ADMIN_PASSWORD is still a factory default — change it in Railway immediately."
        )