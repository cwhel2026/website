# Production deploy (authoritative) — SurfaceCoat / Revive My Drive

**Single production profile for the public website + admin login** on Railway.

## Railway service: `website`

| Setting | Value |
|---------|--------|
| **Root directory** | *(empty — repository root)* |
| **Config file path** | `/railway.toml` |
| **Dockerfile path** | `apps/combined/Dockerfile` (or repo-root `Dockerfile`, same image) |
| **Start command** | `/app/start.sh` or empty (image `CMD`) |
| **Health check** | *(disabled)* — use `/api/live` (liveness) and `/api/ready` (readiness) manually |

Optional variable: `RAILWAY_DOCKERFILE_PATH=apps/combined/Dockerfile`

Do **not** use Root Directory `apps/web` for production login (isolated context cannot include `apps/api`).

## Runtime layout (combined container)

| Process | Bind | Role |
|---------|------|------|
| Next.js | `0.0.0.0:$PORT` | Public site (Railway routes traffic here) |
| FastAPI (uvicorn) | `127.0.0.1:8000` | API; proxied via Next rewrites + `/api/v1/*` routes |

`API_INTERNAL_URL` must be `http://127.0.0.1:8000` **without a trailing slash** (startup script strips one if present).
| Alembic | always on start (`python -m app.schema.cli upgrade`); start fails closed | Additive only; never resets data |

Startup logs: prefix `[rmd]`, `[rmd-web]`, `[rmd-api]` on stdout (Railway deploy logs).

## Required environment (same service)

| Variable | Notes |
|----------|--------|
| `DATABASE_URL` | Railway Postgres (`postgresql://…` normalised to asyncpg + psycopg3) |
| `JWT_SECRET` | 32+ chars when `ENVIRONMENT=production` |
| `ENVIRONMENT` | `production` |
| `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` | Owner login (synced on boot; no DB reset) |
| `CORS_ORIGINS` | `https://<your>.up.railway.app` |
| `PUBLIC_API_BASE_URL` | Same public URL |

Migrations: applied automatically on start. Run `python -m app.schema.cli dry-run` against production before deploying (see `MIGRATIONS.md`).

## Health endpoints

| URL | Meaning |
|-----|---------|
| `GET /api/live` | **Liveness** — Next.js only (must return 200 when container is up) |
| `GET /health` | FastAPI **liveness** (proxied in combined build) |
| `GET /ready` | FastAPI **readiness** — DB `SELECT 1` |
| `GET /api/ready` | **Stack readiness** — combined image + API health + DB |
| `GET /api/ops/status` | Operator JSON (sidecar reachable, no secrets) |

## Verification checklist (production URL)

Replace `BASE` with `https://website-production-c21e95cd.up.railway.app`:

1. `GET BASE/` → 200 HTML  
2. `GET BASE/api/live` → `status: ok`, `hostname: 0.0.0.0`  
3. `GET BASE/health` → JSON `status: ok`  
4. `GET BASE/ready` → `database: ok`  
5. `GET BASE/api/ready` → `status: ready`  
6. `POST BASE/api/v1/auth/login` invalid body → 401/422 (not 503)  
7. Valid owner credentials → 200 + token; dashboard loads  

## Local / CI

```bash
docker build -f apps/combined/Dockerfile -t rmd-combined:local .
# See scripts/smoke-combined-container.sh
```

## Other files (not production website)

| File | Purpose |
|------|---------|
| `apps/web/Dockerfile` | Web-only image if Root = `apps/web` (marketing only) |
| `apps/api/Dockerfile` | Separate API worker/service |
| `RAILWAY_VARIABLES.md` | Extended env reference |

Legacy guides `RAILWAY_LOGIN_FIX.md`, `RAILWAY_FIX_NOW.md` — see this document first.