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
from sqlalchemy import create_engine

from app.config import get_settings
from app.schema.audit import schema_report

ROOT = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


def _engine():
    return create_engine(get_settings().sync_database_url, future=True)


def status() -> int:
    with _engine().connect() as conn:
        report = schema_report(conn)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["ok"] else 1


def dry_run() -> int:
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
    command.upgrade(_alembic_config(), "head")
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
