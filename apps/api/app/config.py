from decimal import Decimal
from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db_urls import derive_sync_from_async, normalize_async_database_url, normalize_sync_database_url


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
    admin_setup_key: str | None = None
    e2e_auditor_email: str | None = None
    e2e_auditor_password: str | None = None
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
    google_places_api_key: str | None = None
    meta_page_id: str | None = None
    meta_instagram_actor_id: str | None = None
    meta_webhook_verify_token: str | None = None
    meta_app_secret: str | None = None
    email_inbound_webhook_secret: str | None = None
    meta_pixel_id: str | None = None
    meta_capi_dataset_token: str | None = None
    google_ads_refresh_token: str | None = None
    google_ads_client_id: str | None = None
    google_ads_client_secret: str | None = None
    ga4_property_id: str | None = None
    gsc_site_url: str | None = None
    gbp_account_id: str | None = None
    outreach_from_email: str = "enquiries@revivemydrive.co.uk"
    outreach_from_name: str = "Revive My Drive Ltd"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    marketing_media_dir: str = "/data/marketing_media"
    marketing_ai_image_enabled: bool = False
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
    finance_token_encryption_key: str | None = None
    finance_receipts_dir: str | None = None
    quote_photos_dir: str | None = None
    finance_receipts_backup_dir: str | None = None
    finance_telegram_ingest_key: str | None = None
    finance_receipt_freeagent_attach: bool = False
    finance_receipt_freeagent_expense: bool = False
    freeagent_default_expense_category_url: str | None = None
    public_dashboard_base_url: str | None = None

    @model_validator(mode="after")
    def normalize_database_urls(self) -> Self:
        self.database_url = normalize_async_database_url(self.database_url)
        sync = (self.sync_database_url or "").strip()
        dev_sync_default = "postgresql://rmd:rmd_dev_password@localhost:5432/revive_my_drive"
        # In production, DATABASE_URL (usually a Railway ${{Postgres.*}} reference) is the only
        # credential source. A hand-typed SYNC_DATABASE_URL often keeps an old password and breaks
        # startup migrations while DATABASE_URL is correct.
        if self.environment.lower() == "production":
            self.sync_database_url = derive_sync_from_async(self.database_url)
            return self
        if not sync or sync == dev_sync_default:
            self.sync_database_url = derive_sync_from_async(self.database_url)
        else:
            self.sync_database_url = normalize_sync_database_url(sync)
        return self

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