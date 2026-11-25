# One Railway service (website + API together)

Use this if you want **one** service and **one** public URL — the setup where you already put all variables on “website”.

## Why the old `apps/web`-only deploy did not work

That container only ran `node server.js`. Python/FastAPI never started, so `TELEGRAM_*`, `DATABASE_URL`, and `JWT_SECRET` on that service were **ignored**.

The **combined** image runs **both**:
- FastAPI on `127.0.0.1:8000` (internal)
- Next.js on `$PORT` (public)
- Next.js proxies `/api/v1/*`, `/health`, `/ready` → FastAPI

Telegram webhook URL becomes:

`https://YOUR-RAILWAY-URL.up.railway.app/api/v1/telegram/webhook`

## Switch your existing website service

1. Open your **website** service in Railway.
2. **Settings → Source → Root directory:** clear it (use **repo root**, not `apps/web`).
3. **Settings → Build → Dockerfile path:** `apps/combined/Dockerfile`  
   (or add a config file — Railway reads `apps/combined/railway.toml` if you set root to `apps/combined` **only if** you copy monorepo paths; **recommended: repo root + dockerfile path above**).

   If Railway only allows root `apps/combined`, set root to **repository root** in the UI (blank or `/`).

4. **Variables** (all on this one service):

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | Leave **empty** or set to your public site URL (same host) |
| `PUBLIC_API_BASE_URL` | **Same** public site URL, e.g. `https://website-production-….up.railway.app` |
| `TELEGRAM_*`, `DATABASE_URL`, `JWT_SECRET`, etc. | Keep everything you already added |
| `CORS_ORIGINS` | Same public site URL |
| `DATABASE_URL` | `postgresql+asyncpg://…` |
| `SYNC_DATABASE_URL` | `postgresql://…` |

5. **Redeploy.**

6. Check `https://YOUR-URL/health` → JSON from FastAPI (proxied).  
   Check `https://YOUR-URL/api/deploy-hint` → web deploy hint.

7. Message Telegram bot — webhook auto-registers on API boot.

## Limits

- **Worker/Celery** still needs a **second** service (or skip background jobs until you add one).
- Heavier image (Node + Python).
- For scale, split **web** + **api** later using [RAILWAY_VARIABLES.md](./RAILWAY_VARIABLES.md).

## Alternative (recommended at scale)

Two services: `apps/web` + `apps/api` — variables split as in RAILWAY_VARIABLES.md.