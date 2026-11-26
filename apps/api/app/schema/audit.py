"""Read-only schema drift audit: live database vs ORM models vs Alembic head."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection

from app.models.registry import load_all_models
from app.schema.reconcile import enum_labels, model_enums

_IGNORED_TABLES = {"alembic_version"}
_BLOCKING = {"add_table", "add_column", "add_index"}


def alembic_head() -> str | None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    return ScriptDirectory.from_config(cfg).get_current_head()


def _describe(diff: Any) -> dict[str, str]:
    if isinstance(diff, list):
        diff = diff[0]
    kind = diff[0]
    obj = diff[1] if len(diff) > 1 else None
    if kind in ("add_table", "remove_table"):
        return {"kind": kind, "object": obj.name}
    if kind in ("add_column", "remove_column"):
        return {"kind": kind, "object": f"{diff[2]}.{diff[3].name}"}
    if kind in ("add_index", "remove_index"):
        return {"kind": kind, "object": f"{obj.table.name}.{obj.name}"}
    if kind.startswith("modify_"):
        return {"kind": kind, "object": f"{diff[2]}.{diff[3]}"}
    return {"kind": kind, "object": str(getattr(obj, "name", obj))}


def schema_report(conn: Connection) -> dict[str, Any]:
    metadata = load_all_models()
    ctx = MigrationContext.configure(conn, opts={"compare_type": False})
    current = ctx.get_current_revision()
    raw = compare_metadata(ctx, metadata)
    diffs = []
    for d in raw:
        info = _describe(d)
        if info["object"].split(".")[0] in _IGNORED_TABLES:
            continue
        diffs.append(info)

    live_enums = enum_labels(conn)
    missing_enum_labels = []
    for name, labels in model_enums(metadata).items():
        if name not in live_enums:
            missing_enum_labels.append({"enum": name, "missing": labels, "type_missing": True})
            continue
        missing = [label for label in labels if label not in live_enums[name]]
        if missing:
            missing_enum_labels.append({"enum": name, "missing": missing, "type_missing": False})

    blocking = [d for d in diffs if d["kind"] in _BLOCKING]
    head = alembic_head()
    return {
        "alembic_current": current,
        "alembic_head": head,
        "at_head": current == head,
        "tables_in_models": len(metadata.tables),
        "tables_in_db": len(
            [t for t in sa.inspect(conn).get_table_names() if t not in _IGNORED_TABLES]
        ),
        "blocking_drift": blocking,
        "other_drift": [d for d in diffs if d["kind"] not in _BLOCKING],
        "missing_enum_labels": missing_enum_labels,
        "ok": current == head and not blocking and not missing_enum_labels,
    }
