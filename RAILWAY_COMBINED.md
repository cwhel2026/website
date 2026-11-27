# One Railway service (website + API together)

**Authoritative deploy checklist:** [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md)

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
| `DATABASE_URL` | **Variable reference** `${{Postgres.DATABASE_URL}}` (app adds `+asyncpg`). On private networking use `${{Postgres.DATABASE_PRIVATE_URL}}` |
| `SYNC_DATABASE_URL` | **Omit in production** — derived automatically from `DATABASE_URL`. Delete it if you added a hand-typed copy (stale passwords cause startup migration failures) |

5. **Redeploy.**

### Database connection errors

If deploy logs show `password authentication failed for user "postgres"` during `python -m app.schema.cli upgrade`:

1. Railway → your **Postgres** plugin → **Connect** → confirm the URL works (user is often `postgres`; the password is **only** in that panel).
2. Railway → **website** service → **Variables**:
   - Set `DATABASE_URL` to **Add variable reference** → Postgres → `DATABASE_URL` or `DATABASE_PRIVATE_URL` (not a pasted string from an old deploy).
   - **Remove** `SYNC_DATABASE_URL` if it is a hand-typed duplicate.
3. Do **not** paste passwords into chat or commit them. Redeploy the website service.

If it still fails after a reference-based `DATABASE_URL`, the Postgres password was rotated: update the reference by redeploying Postgres or resetting credentials in Railway, then redeploy the website service.

6. After deploy finishes, check `https://YOUR-URL/health` → JSON from FastAPI (proxied). Railway HTTP health checks are disabled in config for faster rollouts.  
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