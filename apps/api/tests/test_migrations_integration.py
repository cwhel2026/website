"""Migration path tests against a dedicated, disposable PostgreSQL database.

Requires MIGRATION_TEST_DATABASE_URL pointing at a database whose name ends in
``_migration_test``; the schema is dropped and rebuilt for every test. Never
point this at a real database.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

API_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCHEMA = API_ROOT / "tests" / "fixtures" / "legacy_create_all_schema.sql"
URL = os.getenv("MIGRATION_TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(not URL, reason="MIGRATION_TEST_DATABASE_URL not set")


def _sync_url() -> str:
    db_name = urlparse(URL).path.lstrip("/")
    assert db_name.endswith("_migration_test"), "refusing to reset a non-test database"
    return URL.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.fixture()
def engine(monkeypatch):
    url = _sync_url()
    monkeypatch.setenv("DATABASE_URL", url.replace("+psycopg", "+asyncpg"))
    monkeypatch.setenv("SYNC_DATABASE_URL", url.replace("+psycopg", ""))
    from app.config import get_settings

    get_settings.cache_clear()
    eng = create_engine(url, future=True)
    with eng.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    yield eng
    eng.dispose()
    get_settings.cache_clear()


def _upgrade(eng) -> None:
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    with eng.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")


def _report(eng) -> dict:
    from app.schema.audit import schema_report

    with eng.connect() as conn:
        return schema_report(conn)


def test_empty_database_upgrades_to_head_without_drift(engine):
    _upgrade(engine)
    report = _report(engine)
    assert report["ok"], report
    assert report["tables_in_db"] == report["tables_in_models"]


def test_legacy_create_all_database_is_reconciled_without_data_loss(engine):
    with engine.begin() as conn:
        conn.exec_driver_sql(LEGACY_SCHEMA.read_text())
        conn.execute(
            text(
                "INSERT INTO marketing_budget_policies (id, live_paid_spend_approved, emergency_pause_all, "
                "daily_limit_gbp, weekly_limit_gbp, monthly_limit_gbp, meta_daily_limit_gbp, google_daily_limit_gbp, "
                "max_single_increase_pct, research_api_daily_limit_gbp, outreach_email_enabled, outreach_daily_cap, "
                "updated_at) VALUES (gen_random_uuid(), false, false, 20, 150, 600, 20, 10, 20, 2, false, 20, now())"
            )
        )

    before = _report(engine)
    missing = {d["object"] for d in before["blocking_drift"]}
    assert "marketing_budget_policies.meta_weekly_budget_gbp" in missing
    assert before["alembic_current"] is None

    _upgrade(engine)
    after = _report(engine)
    assert after["ok"], after

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT weekly_limit_gbp, meta_weekly_budget_gbp FROM marketing_budget_policies")
        ).one()
        labels = conn.execute(
            text(
                "SELECT array_agg(enumlabel::text) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
                "WHERE t.typname = 'user_role'"
            )
        ).scalar()
    assert float(row[0]) == 150
    assert row[1] is not None
    assert {"OWNER", "ADMIN", "ACCOUNTANT", "AUDITOR"} <= set(labels)


def test_models_do_not_change_without_a_migration(engine):
    """Frozen baseline (= schema at 0017) + later revisions must equal the models."""
    baseline = API_ROOT / "alembic" / "baseline" / "schema_20261126.sql"
    with engine.begin() as conn:
        conn.exec_driver_sql(baseline.read_text())
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.stamp(cfg, "20261126_0017")
    _upgrade(engine)
    report = _report(engine)
    assert not report["blocking_drift"], (
        "Model changed without an Alembic revision: " + repr(report["blocking_drift"])
    )
    assert not report["missing_enum_labels"], report["missing_enum_labels"]


def test_upgrade_is_idempotent(engine):
    _upgrade(engine)
    _upgrade(engine)
    assert _report(engine)["ok"]
