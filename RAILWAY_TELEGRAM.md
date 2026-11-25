# Railway — Telegram webhook and notifications

Run these steps on the **API** service (FastAPI), not the Next.js **web** service.

## 1. Variables (API service)

| Variable | Required | Notes |
|----------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Yes | From BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | Long random string (≥16 chars); same value used at registration |
| `TELEGRAM_ADMIN_IDS` | Yes | Comma-separated numeric user IDs allowed to chat with the bot |
| `PUBLIC_API_BASE_URL` | Yes* | `https://<your-api-service>.up.railway.app` — **no** trailing slash, **no** `/api/v1` |
| `RAILWAY_PUBLIC_DOMAIN` | Auto | Railway may set this; script uses it if `PUBLIC_API_BASE_URL` is empty |

\*Strongly recommended to set `PUBLIC_API_BASE_URL` explicitly so webhook registration never targets the wrong host.

Optional:

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_OWNER_CHAT_ID` | Pin outbound alert chat (defaults to first `TELEGRAM_ADMIN_IDS` entry via outbox) |

## 2. Variables (worker service)

The worker sends queued Telegram notifications and weather alerts. Copy from **API**:

| Variable | Required |
|----------|----------|
| `SYNC_DATABASE_URL` | Yes |
| `REDIS_URL` | Yes |
| `TELEGRAM_BOT_TOKEN` | Yes |
| `TELEGRAM_ADMIN_IDS` | Yes |
| `ENVIRONMENT=production` | Yes |

The worker does **not** need `TELEGRAM_WEBHOOK_SECRET` (only the API webhook verifies inbound updates).

Ensure the worker start command is:

```bash
celery -A app.worker.celery_app worker --beat --loglevel=info
```

## 3. Register the webhook (one-off)

**Option A — Railway shell (recommended)**

1. Open the **API** service → **Deployments** → latest deployment → **Shell** (or use [Railway CLI](https://docs.railway.app/develop/cli) `railway shell` linked to the API service).
2. Confirm env is loaded: `test -n "$TELEGRAM_BOT_TOKEN" && echo ok`
3. Run:

```bash
cd /app && python scripts/register_telegram_webhook.py
```

If your image working directory is already `apps/api`, use:

```bash
python scripts/register_telegram_webhook.py
```

**Option B — locally with Railway CLI**

```bash
railway link   # select API service
railway run python scripts/register_telegram_webhook.py
```

**Inspect only (no changes):**

```bash
python scripts/register_telegram_webhook.py --info-only
```

**Remove webhook:**

```bash
python scripts/register_telegram_webhook.py --delete
```

The script never prints tokens or secrets; it only shows masked values and public URLs.

## 4. Verify end-to-end

1. `getWebhookInfo` — script prints `url` matching  
   `{PUBLIC_API_BASE_URL}/api/v1/telegram/webhook`
2. `last_error_message` should be empty after registration.
3. From Telegram, send a text message to your bot from a user ID in `TELEGRAM_ADMIN_IDS`.
4. You should get a **real chat reply** (assistant text).
5. In the database: rows in `telegram_processed_updates` and `telegram_conversation_messages` (inbound + outbound).

If you see HTTP 401/403 in Telegram’s `last_error_message`, recheck `TELEGRAM_WEBHOOK_SECRET` on API and re-run registration with the same secret.

## 5. Web app API URL (separate from webhook)

On the **web** service, set **`NEXT_PUBLIC_API_URL`** to the **same API origin** as `PUBLIC_API_BASE_URL`:

```text
NEXT_PUBLIC_API_URL=https://<your-api-service>.up.railway.app
```

**Do not** append `/api/v1`. The Next.js app adds paths such as `/api/v1/auth/login` itself.

After changing `NEXT_PUBLIC_API_URL`, **rebuild and redeploy** the web service (Next.js bakes this in at build time).

Set **`CORS_ORIGINS`** on the API to your public site origin, e.g.:

```text
CORS_ORIGINS=https://website-production-c21e95cd.up.railway.app
```

## 6. Troubleshooting

### “Nothing happens” when I message the bot (messages show ✓✓ but no reply)

Telegram ✓✓ only means the message reached Telegram’s servers — **not** that your API received it.

Work through this list in order:

1. **Webhook registered?** On API shell: `python scripts/register_telegram_webhook.py --info-only`  
   - `url` must be your **API** host + `/api/v1/telegram/webhook` (not the website Next.js URL).  
   - If `url` is empty, run `python scripts/register_telegram_webhook.py`.

2. **`last_error_message` in getWebhookInfo**  
   - Wrong host, SSL, or 401 → fix `PUBLIC_API_BASE_URL` and `TELEGRAM_WEBHOOK_SECRET`, re-register.

3. **Latest API code deployed?** PR #15 changes are required (real `sendMessage`, not JSON-only webhook). Redeploy the **api** service from the branch/commit that includes `app/routers/telegram.py` outbound send.

4. **`TELEGRAM_ADMIN_IDS`** must include **your numeric user ID** (not username).  
   - After the latest handler update, unauthorised users still get a **one-time hint message** with their ID.  
   - Or use [@userinfobot](https://t.me/userinfobot).

5. **Dashboard check (after login):** `GET /api/v1/telegram/status` — shows webhook URL, errors, admin ID count (no secrets).

6. **Database:** migration `20251125_0003` applied (`telegram_processed_updates` table).

| Symptom | Check |
|---------|--------|
| Webhook `last_error_message` SSL / connection | API service public networking enabled; URL is API host not web host |
| 401 on webhook | `TELEGRAM_WEBHOOK_SECRET` mismatch — re-run registration script |
| Hint with user ID but no assistant | Add ID to `TELEGRAM_ADMIN_IDS`, redeploy API |
| No reply at all | Webhook URL empty/wrong — re-run registration script |
| Outbox stuck pending | Worker running; worker has `TELEGRAM_*` and `REDIS_URL` |