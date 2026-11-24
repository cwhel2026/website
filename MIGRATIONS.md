# Database migrations (Alembic)

Production Postgres should use **Alembic** for additive schema changes. The API still runs `create_all` on startup unless you opt out.

## Railway / Docker API deploy

1. Set on the **api** service (after Postgres exists):

   ```text
   DATABASE_MIGRATIONS_MANAGED=true
   SYNC_DATABASE_URL=postgresql://...
   ```

2. **Pre-deploy or start command** (recommended once `create_all` has already bootstrapped tables):

   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

   For the stock Dockerfile CMD, override the Railway **custom start command** as above (from `apps/api` root).

3. **Worker** — same `SYNC_DATABASE_URL`; run migrations from the **api** service only (not the worker).

## Local

```bash
cd apps/api
export SYNC_DATABASE_URL=postgresql://rmd:rmd_dev_password@localhost:5432/revive_my_drive
alembic upgrade head
```

## Revisions

| Revision | Purpose |
|----------|---------|
| `20251124_0001` | Placeholder (schema historically from `create_all`) |
| `20251124_0002` | FreeAgent OAuth token columns on `freeagent_connections` |

New environments with empty Postgres can still use `create_all` once, then `alembic stamp head` before enabling `DATABASE_MIGRATIONS_MANAGED`.