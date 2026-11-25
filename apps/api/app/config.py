from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://rmd:rmd_dev_password@localhost:5432/revive_my_drive"
    )
    sync_database_url: str = (
        "postgresql://rmd:rmd_dev_password@localhost:5432/revive_my_drive"
    )
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    default_admin_email: str = "admin@revivemydrive.co.uk"
    default_admin_password: str = "ChangeMe-RMD-2025!"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    google_ai_api_key: str | None = None
    ai_provider: str = "auto"
    ai_daily_spend_limit_gbp: Decimal = Decimal("2.50")
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None
    telegram_admin_ids: str = ""
    public_api_base_url: str | None = None
    telegram_owner_chat_id: int | None = None
    notification_morning_briefing_time: str = "06:30"
    notification_timezone: str = "Europe/London"
    telegram_auto_register_webhook: bool = True
    telegram_webhook_setup_key: str | None = None
    global_emergency_stop: bool = False
    meta_access_token: str | None = None
    meta_ad_account_id: str | None = None
    google_ads_customer_id: str | None = None
    google_ads_developer_token: str | None = None
    companies_house_api_key: str | None = None
    marketing_media_dir: str = "data/marketing_media"
    marketing_simulation_default: bool = True
    freeagent_client_id: str | None = None
    freeagent_client_secret: str | None = None
    freeagent_redirect_uri: str | None = None
    git_commit: str = "unknown"
    build_time: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    weather_provider: str = "openmeteo"
    weather_simulation_fallback: bool = True
    weather_allow_simulation_for_booking: bool = False
    freeagent_api_base: str = "https://api.freeagent.com"
    rate_limit_storage_redis: bool = False
    database_migrations_managed: bool = False
    finance_token_encryption_key: str | None = None
    finance_receipts_dir: str | None = None
    finance_receipts_backup_dir: str | None = None
    finance_telegram_ingest_key: str | None = None
    finance_receipt_freeagent_attach: bool = False
    finance_receipt_freeagent_expense: bool = False
    freeagent_default_expense_category_url: str | None = None
    public_dashboard_base_url: str | None = None

    @property
    def telegram_admin_id_list(self) -> list[int]:
        if not self.telegram_admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.telegram_admin_ids.split(",") if x.strip().isdigit()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()