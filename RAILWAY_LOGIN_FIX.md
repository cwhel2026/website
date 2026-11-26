# Fix dashboard login (all variables on “website”)

You can keep **every variable on the website Railway service** — but the service must run the **combined** image (Next.js + FastAPI in one container), not `apps/web` alone.

## One-time Railway change (fixes 502 + login)

Railway **cannot** build the combined image when **Root Directory = `apps/web`**: the API (`apps/api`) is outside that folder, so Docker never ships FastAPI. A stale or mismatched image plus **Start command `/app/start.sh`** on a broken build → **“Application failed to respond”**.

### Required for combined (site + API + login)

1. **Settings → Root Directory:** **empty** (repository root — not `apps/web`).
2. **Settings → Config file path:** `/railway.toml` (repo root).
3. **Settings → Build → Dockerfile path:** `apps/combined/Dockerfile` (or variable `RAILWAY_DOCKERFILE_PATH=apps/combined/Dockerfile`).
4. **Settings → Deploy → Start command:** `/app/start.sh` or leave empty (image `CMD`).
5. **Health check path (optional):** `/api/live` (60s) or empty in the UI.
6. **Redeploy** from latest `main`.

### If Root Directory stays `apps/web`

You get **web-only** (public marketing site). Config path `/apps/web/railway.toml`, Dockerfile `Dockerfile` in that folder. **`/api/live` works; `/health` and login do not.** To restore the dashboard, switch to the combined steps above.

Keep on this same service:

- `DATABASE_URL`, `SYNC_DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production` (`postgresql://…` URLs are auto-normalised to asyncpg + psycopg3)
- `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD` (the email/password you use on the login screen)
- `CORS_ORIGINS` = your public site URL, e.g. `https://website-production-….up.railway.app`
- `PUBLIC_API_BASE_URL` = same URL (for Telegram)
- `NEXT_PUBLIC_API_URL` = **empty** or the same site URL (not a separate API host unless you added a second service)
- All other keys (`OPENAI_*`, `TELEGRAM_*`, finance, marketing, etc.)

## Verify

| URL | Expected |
|-----|----------|
| `/health` | JSON `status` from FastAPI |
| `/api/ops/status` | `combined_sidecar: true`, `api.reachable: true` |
| `/api/deploy-hint` | `combined_deploy: true` |

## Sign in

Use exactly **`DEFAULT_ADMIN_EMAIL`** and **`DEFAULT_ADMIN_PASSWORD`** from Railway. On each API boot, the owner account for that email is created or its password is synced from the env var.

## `ECONNREFUSED 127.0.0.1:8000` in logs

The combined image is running, but **uvicorn exited or never started**. Open **Deployments → View logs** and search for `uvicorn exited` or the FastAPI traceback.

Common causes on Railway:

| Issue | Fix |
|-------|-----|
| Missing `SYNC_DATABASE_URL` | Add `postgresql://…` (same DB as `DATABASE_URL`, without `+asyncpg`) |
| `JWT_SECRET` &lt; 32 chars with `ENVIRONMENT=production` | Set a long random secret |
| `DEFAULT_ADMIN_PASSWORD` still `ChangeMe-RMD-2025!` in production | Set a real password in Railway |
| Postgres plugin not linked / wrong `DATABASE_URL` | Reference Railway Postgres variables on the website service |

After fixing variables, **redeploy**. The container will not start Next.js until `/health` returns OK (so a broken API fails fast with logs).

## Railway “Application failed to respond” (502)

Nothing listened on `$PORT`. Most common on this repo:

1. **Root Directory = `apps/web`** but **Start command = `/app/start.sh`** on an old combined/wrong image (no `server.js` or no `start.sh`).
2. **Combined Dockerfile** with **Root = `apps/web`** (build context missing `apps/api` — failed or cached wrong image).
3. Alembic/`set -e` exit before Node (mitigated in current `start.sh`).

**Fix:** clear Root Directory → `/railway.toml` → `apps/combined/Dockerfile` → redeploy.

**Latest `start.sh`:** Next.js binds `$PORT` first; FastAPI + Alembic run in the background. Redeploy from current `main`.

Smoke test after deploy: `GET /api/live` → `{"status":"ok","layer":"web"}` (does not need the API). Then `GET /health` for FastAPI.

In **Deployments → View logs**, look for:

| Log line | Meaning |
|----------|---------|
| `uvicorn exited before ready` | Python crash (imports, `JWT_SECRET` too short with `ENVIRONMENT=production`, DB driver) |
| Login/API 503 for ~30s after deploy | Normal while uvicorn starts in background — retry `/health` then login |
| `Alembic failed` | Bad `SYNC_DATABASE_URL` or revision conflict — see `MIGRATIONS.md` |
| `Wrong Dockerfile for production` | Dockerfile path still `apps/web/Dockerfile` — use `apps/combined/Dockerfile` |

After merge, redeploy from latest `main`. Optional: `ALEMBIC_ON_START=1` on the website service to apply revisions **0015–0016** on boot (only if Alembic history is already in sync).

## Still failing?

- Wrong email (e.g. personal Yahoo) if `DEFAULT_ADMIN_EMAIL` is something else.
- `DEFAULT_ADMIN_PASSWORD` changed in Railway but old session — redeploy and try again.
- `JWT_SECRET` too short in production — use 32+ random characters.