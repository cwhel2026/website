from app.config import Settings
from app.db_urls import normalize_async_database_url, normalize_sync_database_url


def test_railway_style_async_url():
    raw = "postgresql://user:pass@containers-us-west-1.railway.app:5432/railway"
    assert (
        normalize_async_database_url(raw)
        == "postgresql+asyncpg://user:pass@containers-us-west-1.railway.app:5432/railway"
    )


def test_sync_url_uses_psycopg_not_psycopg2():
    raw = "postgresql://user:pass@host:5432/db"
    assert normalize_sync_database_url(raw) == "postgresql+psycopg://user:pass@host:5432/db"


def test_sync_strips_asyncpg_from_sync_env():
    assert (
        normalize_sync_database_url("postgresql+asyncpg://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )


def test_settings_normalizes_both_urls():
    s = Settings(
        database_url="postgresql://a:b@db.example.com:5432/prod",
        sync_database_url="postgresql://a:b@db.example.com:5432/prod",
    )
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.sync_database_url.startswith("postgresql+psycopg://")