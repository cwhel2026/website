"""Additive reconciliation of a live database against the ORM models.

Only ever *adds* missing objects (tables, columns, indexes, enum labels).
It never drops, renames, retypes or rewrites data. Anything it cannot add
safely is reported so an operator can decide.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import sqlalchemy as sa
from sqlalchemy.engine import Connection

logger = logging.getLogger("alembic.reconcile")


@dataclass
class ReconcileReport:
    tables_created: list[str] = field(default_factory=list)
    columns_added: list[str] = field(default_factory=list)
    columns_added_nullable: list[str] = field(default_factory=list)
    indexes_created: list[str] = field(default_factory=list)
    enum_labels_added: list[str] = field(default_factory=list)


def enum_labels(conn: Connection) -> dict[str, list[str]]:
    rows = conn.execute(
        sa.text(
            "SELECT t.typname, e.enumlabel FROM pg_type t "
            "JOIN pg_enum e ON e.enumtypid = t.oid "
            "JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE n.nspname = current_schema() ORDER BY t.typname, e.enumsortorder"
        )
    ).all()
    out: dict[str, list[str]] = {}
    for name, label in rows:
        out.setdefault(name, []).append(label)
    return out


def model_enums(metadata: sa.MetaData) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for table in metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, sa.Enum) and col.type.name and col.type.native_enum:
                out.setdefault(col.type.name, list(col.type.enums))
    return out


def _scalar_default(col: sa.Column):
    default = col.default
    if default is None or not getattr(default, "is_scalar", False):
        return None
    value = default.arg
    if hasattr(value, "name") and isinstance(col.type, sa.Enum):
        return value.name
    return value


def reconcile(conn: Connection, metadata: sa.MetaData) -> ReconcileReport:
    report = ReconcileReport()
    dialect = conn.dialect
    preparer = dialect.identifier_preparer

    existing_enums = enum_labels(conn)
    for name, labels in model_enums(metadata).items():
        if name not in existing_enums:
            continue
        for label in labels:
            if label not in existing_enums[name]:
                conn.exec_driver_sql(
                    f"ALTER TYPE {preparer.quote(name)} ADD VALUE IF NOT EXISTS '{label}'"
                )
                report.enum_labels_added.append(f"{name}.{label}")

    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    for table in metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(conn, checkfirst=True)
            report.tables_created.append(table.name)
            continue
        live_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in live_cols:
                continue
            if isinstance(col.type, sa.Enum) and col.type.native_enum:
                col.type.create(conn, checkfirst=True)
            ddl_type = col.type.compile(dialect=dialect)
            stmt = f"ALTER TABLE {preparer.quote(table.name)} ADD COLUMN {preparer.quote(col.name)} {ddl_type}"
            default = _scalar_default(col)
            server_default = col.server_default.arg if col.server_default is not None else None
            if server_default is not None:
                text = server_default.text if hasattr(server_default, "text") else str(server_default)
                stmt += f" DEFAULT {text}"
            elif default is not None:
                literal = sa.literal(default, type_=col.type).compile(
                    dialect=dialect, compile_kwargs={"literal_binds": True}
                )
                stmt += f" DEFAULT {literal}"
            can_be_not_null = server_default is not None or default is not None
            if not col.nullable and can_be_not_null:
                stmt += " NOT NULL"
            conn.exec_driver_sql(stmt)
            if default is not None and server_default is None:
                conn.exec_driver_sql(
                    f"ALTER TABLE {preparer.quote(table.name)} ALTER COLUMN {preparer.quote(col.name)} DROP DEFAULT"
                )
            label = f"{table.name}.{col.name}"
            if not col.nullable and not can_be_not_null:
                report.columns_added_nullable.append(label)
            report.columns_added.append(label)
            if col.unique and not col.index:
                conn.exec_driver_sql(
                    f"ALTER TABLE {preparer.quote(table.name)} ADD UNIQUE ({preparer.quote(col.name)})"
                )
            for fk in col.foreign_keys:
                target = fk.column
                conn.exec_driver_sql(
                    f"ALTER TABLE {preparer.quote(table.name)} ADD FOREIGN KEY ({preparer.quote(col.name)}) "
                    f"REFERENCES {preparer.quote(target.table.name)} ({preparer.quote(target.name)})"
                    + (f" ON DELETE {fk.ondelete}" if fk.ondelete else "")
                )
        live_indexes = {ix["name"] for ix in sa.inspect(conn).get_indexes(table.name)}
        for index in table.indexes:
            if index.name and index.name not in live_indexes:
                index.create(conn, checkfirst=True)
                report.indexes_created.append(index.name)

    for kind in ("enum_labels_added", "tables_created", "columns_added", "indexes_created"):
        for item in getattr(report, kind):
            logger.info("reconcile %s: %s", kind, item)
    for item in report.columns_added_nullable:
        logger.warning("reconcile: %s added as NULLABLE (model says NOT NULL, no default)", item)
    return report
