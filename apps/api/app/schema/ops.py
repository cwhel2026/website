"""Existence-checked Alembic operations.

Production databases were originally built by ``Base.metadata.create_all`` at
API startup, so historical revisions must tolerate objects that already exist.
Every revision uses these wrappers instead of the raw ``op.create_*`` /
``op.add_column`` calls so ``alembic upgrade head`` is safe on both empty and
legacy databases.
"""

from __future__ import annotations

import logging

import sqlalchemy as sa
from alembic import op

logger = logging.getLogger("alembic.safe_ops")


def _inspector() -> sa.engine.reflection.Inspector:
    return sa.inspect(op.get_bind())


def table_exists(name: str) -> bool:
    return _inspector().has_table(name)


def column_exists(table: str, column: str) -> bool:
    if not table_exists(table):
        return False
    return any(c["name"] == column for c in _inspector().get_columns(table))


def index_exists(table: str, name: str) -> bool:
    if not table_exists(table):
        return False
    return any(ix["name"] == name for ix in _inspector().get_indexes(table))


def _live_enum_labels(type_name: str) -> list[str] | None:
    rows = op.get_bind().execute(
        sa.text(
            "SELECT e.enumlabel FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid "
            "WHERE t.typname = :n ORDER BY e.enumsortorder"
        ),
        {"n": type_name},
    ).all()
    return [r[0] for r in rows] or None


def _align_enum_default(column: sa.Column) -> None:
    """Map a lowercase enum server_default onto the live label.

    Types created by ``create_all`` use member names (``DISCOVERED``) while the
    historical revisions assumed values (``discovered``).
    """
    if not isinstance(column.type, sa.Enum) or column.server_default is None:
        return
    arg = getattr(column.server_default, "arg", None)
    if not isinstance(arg, str) or not column.type.name:
        return
    labels = _live_enum_labels(column.type.name)
    if labels and arg not in labels and arg.upper() in labels:
        logger.info("enum default %s -> %s for %s", arg, arg.upper(), column.name)
        column.server_default = sa.DefaultClause(arg.upper())


def create_table(name: str, *columns, **kw) -> None:
    if table_exists(name):
        logger.info("skip create_table %s (exists)", name)
        return
    for col in columns:
        if isinstance(col, sa.Column):
            _align_enum_default(col)
    op.create_table(name, *columns, **kw)


def add_column(table: str, column: sa.Column, **kw) -> None:
    if column_exists(table, column.name):
        logger.info("skip add_column %s.%s (exists)", table, column.name)
        return
    _align_enum_default(column)
    op.add_column(table, column, **kw)


def create_index(name: str, table: str, columns, **kw) -> None:
    if index_exists(table, name):
        logger.info("skip create_index %s (exists)", name)
        return
    op.create_index(name, table, columns, **kw)
