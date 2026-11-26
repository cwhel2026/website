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

**Login broken with all variables on website?** See **[RAILWAY_LOGIN_FIX.md](./RAILWAY_LOGIN_FIX.md)**.

## Switch your existing website service (variables stay where they are)

You **do not** need to move env vars off “website”. You only change **how the image is built** (two clicks):

1. Open your **website** service in Railway.
2. **Settings → Source → Root directory:** delete `apps/web` so it is **empty** (repository root). This is required so the build can include both `apps/web` and `apps/api` — the same as shipping frontend + API from one repo in other projects.
3. Redeploy. Railway will use the repo-root **`railway.toml`**, which builds **`apps/combined/Dockerfile`** (one container: Next + FastAPI).
4. **Variables** (keep on this service — no shuffle):

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

## Web-only fallback (root still `apps/web`)

If you **cannot** switch root directory yet, **`main`** includes a **Next.js** Telegram webhook at  
`/api/v1/telegram/webhook` that uses the same `TELEGRAM_*` variables on the **website** service (auto-registers on container start). Dashboard/DB features still need the combined or separate API later.

---

## Limits

- **Worker/Celery** still needs a **second** service (or skip background jobs until you add one).
- Heavier image (Node + Python).
- For scale, split **web** + **api** later using [RAILWAY_VARIABLES.md](./RAILWAY_VARIABLES.md).

## Alternative (recommended at scale)

Two services: `apps/web` + `apps/api` — variables split as in RAILWAY_VARIABLES.md.