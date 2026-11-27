"""Schema operations CLI.

    python -m app.schema.cli status     # read-only drift report (JSON)
    python -m app.schema.cli dry-run    # run `alembic upgrade head` inside a transaction, report, ROLL BACK
    python -m app.schema.cli upgrade    # alembic upgrade head, then verify no blocking drift

PostgreSQL DDL is transactional, so ``dry-run`` shows exactly what an upgrade
would change on the target database without committing anything.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.db_urls import database_target_label
from app.schema.audit import schema_report

ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


def _exit_on_db_error(exc: BaseException) -> None:
    settings = get_settings()
    target = database_target_label(settings.sync_database_url)
    hint = (
        "Postgres rejected the password. On Railway: Postgres service → Connect → use a "
        "**variable reference** on the website service: DATABASE_URL = ${{Postgres.DATABASE_URL}} "
        "(private networking: ${{Postgres.DATABASE_PRIVATE_URL}}). "
        "Delete any hand-typed SYNC_DATABASE_URL — in production it is derived from DATABASE_URL. "
        "See RAILWAY_COMBINED.md § Database connection errors."
    )
    print(
        f"FATAL: cannot connect to database ({target}).\n{hint}\n"
        f"Driver error: {getattr(exc, 'orig', exc)}",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


def _ensure_database_reachable() -> None:
    try:
        with create_engine(get_settings().sync_database_url, future=True).connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        _exit_on_db_error(exc)


def _engine():
    return create_engine(get_settings().sync_database_url, future=True)


def status() -> int:
    _ensure_database_reachable()
    with _engine().connect() as conn:
        report = schema_report(conn)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["ok"] else 1


def dry_run() -> int:
    _ensure_database_reachable()
    engine = _engine()
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            before = schema_report(conn)
            cfg = _alembic_config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
            after = schema_report(conn)
        finally:
            trans.rollback()
    print(json.dumps({"before": before, "after_upgrade_rolled_back": after}, indent=2, default=str))
    return 0 if after["ok"] else 1


def upgrade() -> int:
    _ensure_database_reachable()
    try:
        command.upgrade(_alembic_config(), "head")
    except OperationalError as exc:
        _exit_on_db_error(exc)
    with _engine().connect() as conn:
        report = schema_report(conn)
    print(json.dumps(report, indent=2, default=str))
    if not report["ok"]:
        print("Schema drift remains after upgrade", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    cmd = argv[1] if len(argv) > 1 else "status"
    handlers = {"status": status, "dry-run": dry_run, "upgrade": upgrade}
    if cmd not in handlers:
        print(__doc__)
        return 2
    return handlers[cmd]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
