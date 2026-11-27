from app.config import Settings
from app.db_urls import database_target_label, derive_sync_from_async


def test_production_derives_sync_from_database_url(monkeypatch):
    monkeypatch.delenv("SYNC_DATABASE_URL", raising=False)
    async_url = "postgresql+asyncpg://postgres:secret@10.0.0.1:5432/railway"
    wrong_sync = "postgresql://postgres:wrong-password@10.0.0.1:5432/railway"
    s = Settings(
        environment="production",
        database_url=async_url,
        sync_database_url=wrong_sync,
    )
    assert "wrong-password" not in s.sync_database_url
    assert s.sync_database_url.startswith("postgresql+psycopg://postgres:")
    assert "10.0.0.1:5432/railway" in s.sync_database_url


def test_database_target_label_hides_password():
    label = database_target_label("postgresql://postgres:supersecret@host.internal:5432/railway")
    assert "supersecret" not in label
    assert "postgres" in label and "host.internal" in label and "railway" in label


def test_development_keeps_explicit_sync(monkeypatch):
    monkeypatch.delenv("SYNC_DATABASE_URL", raising=False)
    s = Settings(
        environment="development",
        database_url="postgresql+asyncpg://rmd:async@localhost:5432/revive_my_drive",
        sync_database_url="postgresql://rmd:sync@localhost:5432/revive_my_drive",
    )
    assert "sync@localhost" in s.sync_database_url