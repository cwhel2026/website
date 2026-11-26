# Database migrations (Alembic)

Alembic is the **only** schema authority. The API never calls `create_all`; every process that
starts the API (combined image `start.sh`, API `Dockerfile`) runs

```bash
python -m app.schema.cli upgrade
```

first and refuses to start if it fails. `/ready` returns `503 {"detail":"schema"}` while the database
is not at the Alembic head, and `GET /api/v1/ops/schema` (admin / auditor) reports the exact state.

## How the chain handles each kind of database

| Database | What happens |
|----------|--------------|
| Empty | `20251124_0001` loads the frozen baseline `alembic/baseline/schema_20261126.sql` (current models), later revisions detect the baseline and skip. |
| Legacy, built by `create_all` (current production) | `0001` is a no-op, `0002`–`0016` use existence-checked operations (`app/schema/ops.py`), and `20261126_0017` adds anything still missing by comparing the live schema with the models (`app/schema/reconcile.py`). |
| Already at head | Nothing. Running upgrade repeatedly is safe. |

Reconciliation is **additive only**: it creates missing tables, columns, indexes, constraints and enum
labels. It never drops, renames or rewrites existing data. New NOT NULL columns on populated tables get
a temporary default so existing rows stay valid.

## Before deploying to production

Run the dry run against the production database. It applies the full upgrade inside one transaction,
prints the before/after report, then **rolls back** (Postgres DDL is transactional):

```bash
cd apps/api
SYNC_DATABASE_URL='postgresql://…' python -m app.schema.cli dry-run
```

On Railway: open the website service → **⋯ → Shell** (or `railway run`), then run the command above
from `/api`. Check `after.ok` is `true`. Then deploy normally; the start script applies the same upgrade.

Other commands:

```bash
python -m app.schema.cli status    # read-only report: revision, head, drift
python -m app.schema.cli upgrade   # what start.sh runs
```

## Local

```bash
cd apps/api
export SYNC_DATABASE_URL=postgresql://rmd:rmd_dev_password@localhost:5432/revive_my_drive
python -m app.schema.cli upgrade
```

## Adding a migration

1. Change the model.
2. `alembic revision -m "describe change"` and write the operation with `from app.schema import ops as safe`
   helpers (`safe.create_table`, `safe.add_column`, `safe.create_index`) so it is safe on every database.
3. Regenerate the baseline so fresh databases match: dump a migrated database with
   `pg_dump --schema-only --no-owner --no-privileges`, strip `SET`/`set_config`/comment lines, and save
   it over `alembic/baseline/schema_20261126.sql`.
4. CI (`api-integration` → *Migration paths*) proves empty, legacy and idempotent upgrades and fails if
   the models drift from the migrations.

## Removed flags

`DATABASE_MIGRATIONS_MANAGED` and `ALEMBIC_ON_START` no longer exist. Migrations always run on start.
Delete them from Railway variables if present; they are ignored.
