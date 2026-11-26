# Railway 502 — fix in 3 minutes

Symptom: **Application failed to respond** on `website-production-….up.railway.app`.

That means **nothing is listening on `$PORT`**. On this repo it is almost always **Railway service settings**, not “wrong password”.

## Pick one profile

### A — Full site + dashboard login (recommended)

| Setting | Value |
|---------|--------|
| **Root directory** | *(empty — repository root)* |
| **Config file path** | `/railway.json` or `/railway.toml` |
| **Dockerfile path** | `Dockerfile` or `apps/combined/Dockerfile` |
| **Custom start command** | *(empty)* or `/app/start.sh` |
| **Health check path** | *(empty / disabled)* |

Then **Redeploy** latest `main`. Open deploy **logs** and search for `[rmd]` — you should see `combined start PORT=…`.

Check:

1. `GET /api/live` → `{"status":"ok","layer":"web",…}`
2. `GET /health` → FastAPI JSON
3. `GET /api/deploy-hint` → `combined_deploy: true`

### B — Root stuck on `apps/web` (marketing site only)

| Setting | Value |
|---------|--------|
| **Root directory** | `apps/web` |
| **Config file path** | `/apps/web/railway.json` |
| **Dockerfile path** | `Dockerfile` |
| **Health check path** | *(empty)* |

Public pages and `GET /api/live` work. **Login will not** until you switch to profile **A**.

## Variables (stay on the website service)

- `DATABASE_URL`, `JWT_SECRET` (32+ chars if `ENVIRONMENT=production`)
- `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`
- `CORS_ORIGINS` = your `https://…up.railway.app` URL

## If deploy logs show

| Line | Action |
|------|--------|
| `FATAL: ./server.js missing` | Docker build failed — fix Dockerfile path / root directory |
| `WARN: /api missing` | Profile A not applied — clear root directory |
| `Wrong Dockerfile for production` | Old build — set Dockerfile to repo root `Dockerfile` |

## Why health checks were disabled

A deploy health check on `/health` or `/api/live` while an old image was running caused **no healthy replica** → 502 for the whole URL. Config now sets `healthcheckPath` empty / `null`.