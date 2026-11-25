# Railway — Redis + Celery worker (Stage 3)

**Prerequisite:** `main` includes [PR #11](https://github.com/cwhel2026/website/pull/11) (weather + Celery).

You already added **Redis**. You need **four running services**: Postgres, Redis, **api**, **worker**, and **web** (Postgres + Redis are plugins; three are your repo).

## 1. Link Redis to API and worker

On the **api** and **worker** services → **Variables** → **Add variable reference** → pick your Redis service → choose **`REDIS_URL`** (or `REDIS_PRIVATE_URL` if that is what Railway exposes).

Optional (same value as `REDIS_URL`):

```text
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
```

If you only set `REDIS_URL`, the app already uses it as the Celery broker.

**Web does not need Redis.**

## 2. `SYNC_DATABASE_URL` (API + worker)

Railway Postgres usually gives a URL like:

```text
postgresql://user:pass@host.railway.app:5432/railway
```

| Variable | Service | Value |
|----------|---------|--------|
| `DATABASE_URL` | **api** | Same URL with **`+asyncpg`** after `postgresql`: `postgresql+asyncpg://user:pass@...` |
| `SYNC_DATABASE_URL` | **api** and **worker** | Plain sync URL: `postgresql://user:pass@...` (reference `${{Postgres.DATABASE_URL}}` or paste the URL) |

The **worker** does not need `+asyncpg`; it only needs `SYNC_DATABASE_URL` (and the other vars below).

## 3. Add a **worker** service (clone API)

1. **New service** → same GitHub repo `cwhel2026/website`, branch **`main`**.
2. **Settings → Source → Root directory:** `apps/api`
3. **Settings → Build:** Dockerfile (same as API).
4. **Settings → Deploy → Custom start command:**

   ```bash
   celery -A app.worker.celery_app worker --beat --loglevel=info
   ```

5. **Turn off HTTP health check** for this service (it is not a web server). In Railway: Deploy → disable healthcheck, or leave healthcheck empty.

6. **Variables:** copy from **api** at minimum:

   - `SYNC_DATABASE_URL`
   - `REDIS_URL` (reference)
   - `ENVIRONMENT=production`
   - `JWT_SECRET` (same as API — harmless if copied)
   - Any others you already use on API (Open-Meteo needs no key)

Easiest: use Railway **shared variables** for the whole project so api + worker stay in sync.

## 4. API service (extra vars only)

On **api**, add (if not already):

- `REDIS_URL` (reference from Redis)
- `SYNC_DATABASE_URL` (sync Postgres URL)

Keep existing: `DATABASE_URL` (async), `JWT_SECRET`, `CORS_ORIGINS`, `ENVIRONMENT=production`, etc.

## 5. Redeploy

1. Redeploy **api**
2. Redeploy **worker**
3. Redeploy **web** (no Redis changes)

## 6. Quick checks

| Check | How |
|-------|-----|
| API healthy | `GET https://<api>/health` and `/ready` |
| Workers registered | Dashboard → **Automations** → last run times update after a few minutes |
| Manual run | `POST /api/v1/automations/workers/trigger/refresh_weather_hq` (authenticated) |

## Mental model

```text
Postgres ──┬── api (uvicorn) ── web
           └── worker (celery + beat)
Redis ─────── api + worker (queue)
```

One beat scheduler: run **only one** worker service with `--beat` (do not start beat on two replicas).