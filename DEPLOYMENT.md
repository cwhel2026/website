# Deployment

Target: **Railway** (or any Docker host) with separate **web** and **api** services.

## Checklist before first production deploy

1. Set `ENVIRONMENT=production`, `JWT_SECRET` (≥32 random chars), and change `DEFAULT_ADMIN_PASSWORD`.
2. Point `DATABASE_URL` at managed PostgreSQL (enable PostGIS when you need geometry).
3. Set `CORS_ORIGINS` to your public dashboard origin(s).
4. Set `NEXT_PUBLIC_API_URL` to the public API URL used by the browser.
5. Run integration smoke: `RUN_INTEGRATION_TESTS=1 pytest tests/test_smoke_integration.py -q` in `apps/api`.
6. Plan Alembic migrations instead of relying on `create_all` long term.

## Docker Compose (production-shaped local)

```bash
cp .env.example .env
# edit JWT_SECRET, DEFAULT_ADMIN_PASSWORD, POSTGRES_PASSWORD

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

- API: `http://localhost:8000/health`
- Web: `http://localhost:3000`

## Railway service layout

Create **two** services from the same GitHub repo (`cwhel2026/website`), branch **main**.

| Service | Root directory (required) | Build |
|---------|---------------------------|--------|
| `web` | `apps/web` | Dockerfile → `node server.js` |
| `api` | `apps/api` | Dockerfile → uvicorn on `$PORT` |
| `worker` | `apps/api` | Same image → `celery -A app.worker.celery_app worker --beat` |
| `postgres` | (plugin) | Enable PostGIS when needed |
| `redis` | (plugin) | Stage 3 workers + beat |

**Stage 3 (Redis + Celery):** see **[RAILWAY_STAGE3.md](./RAILWAY_STAGE3.md)** for a short Railway checklist (`REDIS_URL`, `SYNC_DATABASE_URL`, worker start command).

### Fix “repo only contains README.md” (Railpack)

That error means Railway is building from the **repository root** before the monorepo layout is visible, or the service has no **Root Directory** set.

1. Open the failing service → **Settings** → **Source** → **Root Directory**.
2. Set `apps/web` for the frontend service (or `apps/api` for the API).
3. **Settings** → **Build** → Builder: **Dockerfile** (each app has `railway.toml` + `Dockerfile`).
4. **Redeploy** (Deployments → three dots → Redeploy). `main` now contains `apps/web/package.json` and Dockerfiles — not README-only.

For the web image build, set variable **`NEXT_PUBLIC_API_URL`** to your public API URL (e.g. `https://<api-service>.up.railway.app`) before deploy. Use the **origin only** — no trailing slash and **no** `/api/v1` suffix (the web app appends `/api/v1/...` on every request).

On the **API** service, set **`PUBLIC_API_BASE_URL`** to the same origin for Telegram webhook registration (`scripts/register_telegram_webhook.py`). See [RAILWAY_TELEGRAM.md](./RAILWAY_TELEGRAM.md).

### Required variables

**API:** `DATABASE_URL`, `SYNC_DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `ENVIRONMENT=production`, `DEFAULT_ADMIN_PASSWORD`

**FreeAgent (optional):** `FREEAGENT_CLIENT_ID`, `FREEAGENT_CLIENT_SECRET`, `FREEAGENT_REDIRECT_URI` → `https://<api-host>/api/v1/finance/freeagent/callback`

**Migrations:** See `MIGRATIONS.md`. Set `DATABASE_MIGRATIONS_MANAGED=true` when using `alembic upgrade head` on deploy.

**Rate limits (multi-instance):** `RATE_LIMIT_STORAGE_REDIS=true` and `REDIS_URL` on API.

**Web build arg / env:** `NEXT_PUBLIC_API_URL`

## Rate limits (public abuse protection)

- `POST /api/v1/quotations/instant` — 12/minute per IP
- `POST /api/v1/auth/login` and `/token` — 30/minute per IP
- `GET /api/v1/marketing/flyer/{slug}` — 60/minute per IP

For multi-instance deploys, replace in-memory limits with Redis-backed limits (not in Phase 7).