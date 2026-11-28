from app.config import Settings

_INSECURE_JWT_DEFAULTS = frozenset(
    {
        "dev-secret-change-in-production",
        "change-me-in-production-use-long-random-string",
    }
)

FACTORY_DEFAULT_PASSWORDS = frozenset({"ChangeMe-RMD-2025!", "change-on-first-login"})


def validate_production_settings(settings: Settings) -> None:
    if settings.environment.lower() != "production":
        return
    secret = settings.jwt_secret.strip()
    if secret in _INSECURE_JWT_DEFAULTS or len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be a unique random string of at least 32 characters in production."
        )
    if "*" in settings.cors_origin_list:
        raise RuntimeError("Wildcard CORS origins are forbidden in production.")
    if settings.default_admin_password in FACTORY_DEFAULT_PASSWORDS:
        import logging

        logging.getLogger(__name__).critical(
            "DEFAULT_ADMIN_PASSWORD is still a factory default: sign-in with it is refused in production. "
            "Set a unique DEFAULT_ADMIN_PASSWORD in Railway and redeploy."
        )
    import logging

    log = logging.getLogger(__name__)
    if len((settings.finance_token_encryption_key or "").strip()) < 32:
        log.critical(
            "FINANCE_TOKEN_ENCRYPTION_KEY is missing or shorter than 32 characters: "
            "FreeAgent connect/refresh is disabled until it is set."
        )
    if not settings.meta_app_secret:
        log.warning("META_APP_SECRET is not set: Meta webhooks will be rejected (503).")