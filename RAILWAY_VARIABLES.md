# Railway — which variables go on which service?

If you put **Telegram**, **database**, or **JWT** variables on the **website (web)** service, they do **nothing** there. Next.js only reads variables prefixed with `NEXT_PUBLIC_` in the browser — the bot, webhooks, and dashboard API all run on the **API** service.

## You need three application services

| Railway service | Repo root directory | Start command |
|-----------------|---------------------|---------------|
| **web** (or “website”) | `apps/web` | Docker default → `node server.js` |
| **api** | `apps/api` | Docker default → `uvicorn` |
| **worker** (optional but recommended) | `apps/api` | `celery -A app.worker.celery_app worker --beat --loglevel=info` |

Plus **Postgres** and **Redis** plugins.

If you only have one service today (the website), either:

- **Option A (one URL, keep one service):** Use the **combined** image — see **[RAILWAY_COMBINED.md](./RAILWAY_COMBINED.md)** (repo root + `apps/combined/Dockerfile`).  
- **Option B (recommended at scale):** **Add an API service**: New service → same repo → root `apps/api` → deploy from `main`.

---

## WEB only (`apps/web`)

Set these on the **website** service. **Redeploy web** after changing `NEXT_PUBLIC_*` (build-time).

| Variable | Example | Notes |
|----------|---------|--------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-API-SERVICE.up.railway.app` | **Origin only** — no `/api/v1` |
| `NEXT_PUBLIC_SITE_URL` | `https://website-production-….up.railway.app` | Canonical public site URL (sitemap, etc.) |
| `NODE_ENV` | `production` | Usually set by Railway |

Optional build metadata: `NEXT_PUBLIC_GIT_COMMIT`, `NEXT_PUBLIC_BUILD_TIME`

**Remove from web** (security + they do not work here):

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ADMIN_IDS`
- `DATABASE_URL`, `SYNC_DATABASE_URL`, `JWT_SECRET`
- `OPENAI_API_KEY`, `FREEAGENT_*`
- `PUBLIC_API_BASE_URL` (API-only)
- `REDIS_URL` (unless you had a reason on API only — web does not use Redis)

Never use `NEXT_PUBLIC_` for secrets.

---

## API only (`apps/api`)

Copy **all** integration and backend variables here from web.

| Category | Variables |
|----------|-----------|
| **Core** | `DATABASE_URL` (`postgresql+asyncpg://…`), `SYNC_DATABASE_URL` (`postgresql://…`), `JWT_SECRET`, `ENVIRONMENT=production`, `CORS_ORIGINS` (your **web** URL), `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD` |
| **Telegram** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ADMIN_IDS`, `PUBLIC_API_BASE_URL` (= same host as `NEXT_PUBLIC_API_URL`), optional `TELEGRAM_OWNER_CHAT_ID` |
| **Migrations** | `DATABASE_MIGRATIONS_MANAGED=true` after you run Alembic |
| **Redis / limits** | `REDIS_URL`, optional `RATE_LIMIT_STORAGE_REDIS=true`, optional `CELERY_BROKER_URL` |
| **AI** | `OPENAI_API_KEY`, optional `AI_DAILY_SPEND_LIMIT_GBP` |
| **FreeAgent** | `FREEAGENT_CLIENT_ID`, `FREEAGENT_CLIENT_SECRET`, `FREEAGENT_REDIRECT_URI` → must be **API** callback URL |
| **Weather** | `WEATHER_PROVIDER=openmeteo` (default) |

After variables are set: **redeploy API** from `main`. Telegram webhook auto-registers on startup when `TELEGRAM_*` and `PUBLIC_API_BASE_URL` are present.

Health check: open `https://YOUR-API-SERVICE.up.railway.app/health` — JSON `{"status":"ok",...}`. If you see an HTML 404 page, you are still on the **web** host.

---

## WORKER (`apps/api` image, different start command)

| Variable | |
|----------|--|
| `SYNC_DATABASE_URL` | |
| `REDIS_URL` | |
| `ENVIRONMENT=production` | |
| `TELEGRAM_BOT_TOKEN` | outbound messages |
| `TELEGRAM_ADMIN_IDS` | |

Same DB/Redis references as API. No HTTP health check on worker.

---

## Quick fix checklist (you put everything on “website”)

1. **Create API service** (if missing): root `apps/api`, branch `main`, Dockerfile build.
2. **Copy variables** from website → API using the tables above (do not delete from web until API works — copy first).
3. On **web**, keep only `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL` (point API URL at the **API** hostname).
4. Set on **API**: `PUBLIC_API_BASE_URL` = same value as `NEXT_PUBLIC_API_URL`.
5. Set **API** `CORS_ORIGINS` = your public website URL (https).
6. **Redeploy API** first, then **rebuild/redeploy web** so `NEXT_PUBLIC_API_URL` is baked in.
7. Message Telegram bot → `/start`.

---

## Railway shared variables (optional)

Project → **Shared variables** for values used on **API + worker** only (e.g. reference Postgres `DATABASE_URL`, `JWT_SECRET`). Do **not** share Telegram or DB secrets into the **web** service unless you enjoy printing them into client bundles by mistake.

---

See also: [RAILWAY_TELEGRAM.md](./RAILWAY_TELEGRAM.md), [RAILWAY_STAGE3.md](./RAILWAY_STAGE3.md), [DEPLOYMENT.md](./DEPLOYMENT.md).