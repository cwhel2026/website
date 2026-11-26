# Fix dashboard login (all variables on “website”)

You can keep **every variable on the website Railway service** — but the service must run the **combined** image (Next.js + FastAPI in one container), not `apps/web` alone.

## One-time Railway change

You can **keep Root directory = `apps/web`** (as in your screenshot). You must use the **combined** Dockerfile and start command.

1. Open your **website** service in Railway.
2. **Settings → Build → Dockerfile path:** `Dockerfile` (repo root — **not** `apps/web/Dockerfile`).
3. **Settings → Deploy → Custom start command:** `/app/start.sh` (not `node server.js`).
4. **Health check path:** `/health` (not `/`).
5. **Redeploy** (pull latest `main` so `apps/web/railway.toml` applies).

**Alternative:** clear **Root directory** (empty) and redeploy — same combined image.

Keep on this same service:

- `DATABASE_URL`, `SYNC_DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production`
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

## Still failing?

- Wrong email (e.g. personal Yahoo) if `DEFAULT_ADMIN_EMAIL` is something else.
- `DEFAULT_ADMIN_PASSWORD` changed in Railway but old session — redeploy and try again.
- `JWT_SECRET` too short in production — use 32+ random characters.