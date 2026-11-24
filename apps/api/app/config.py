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
    telegram_bot_token: str | None = None
    telegram_admin_ids: str = ""
    global_emergency_stop: bool = False

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