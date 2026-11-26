"""Initial schema baseline

Revision ID: 20251124_0001
Revises:
Create Date: 2025-11-24

Two starting points are supported:

* Empty database: load the frozen baseline (``alembic/baseline/schema_20261126.sql``,
  the full schema as of revision 20261126_0017). Revisions 0002-0017 then find
  every object already present and skip. Later revisions apply normally.
* Legacy database (built by the old startup ``create_all``): nothing happens
  here; 0002-0016 add what is missing and 0017 reconciles the remainder
  against the models. No data is modified or dropped.
"""

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "20251124_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CORE_TABLES = ("users", "territories", "customers")
BASELINE_SQL = Path(__file__).resolve().parent.parent / "baseline" / "schema_20261126.sql"
BASELINE_FLAG = "surfacecoat_baseline_bootstrap"


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if any(t in existing for t in _CORE_TABLES):
        return
    if existing - {"alembic_version"}:
        raise RuntimeError(
            "Refusing baseline bootstrap: database has tables but none of the core "
            f"tables {_CORE_TABLES}. Inspect it manually before migrating."
        )
    bind.exec_driver_sql(BASELINE_SQL.read_text())
    bind.info[BASELINE_FLAG] = True


def downgrade() -> None:
    pass
