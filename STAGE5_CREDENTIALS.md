# Stage 5 — owner credentials and permissions

Do **not** paste secrets into chat. Configure these as Railway (or `.env`) variables on the **API** service.

## Telegram (Priority 1)

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_WEBHOOK_SECRET` | Random string; set the same value when calling `setWebhook` with `secret_token` |
| `TELEGRAM_ADMIN_IDS` | Comma-separated numeric Telegram user IDs allowed to message the bot |
| `TELEGRAM_OWNER_CHAT_ID` | Optional pinned private chat ID for outbound alerts |
| `PUBLIC_API_BASE_URL` | FastAPI public origin only, e.g. `https://<api-service>.up.railway.app` (no `/api/v1`) |

Register webhook: run `python scripts/register_telegram_webhook.py` on the **API** service (see [RAILWAY_TELEGRAM.md](./RAILWAY_TELEGRAM.md)).

Webhook URL (derived): `{PUBLIC_API_BASE_URL}/api/v1/telegram/webhook`

## Weather (already live)

Open-Meteo is used without an API key. Review [Open-Meteo terms](https://open-meteo.com/en/terms) for commercial use.

## Meta / Google Ads (Priority 4 — not activated in this stage)

| Integration | Required |
|-------------|----------|
| Meta Marketing API | App ID, app secret, long-lived user token, `ads_read` / `ads_management` (read-only first) |
| Google Ads API | Developer token (approved), OAuth client, manager/customer ID |

No campaigns will run until owner approval flags are enabled in the dashboard.

## OpenAI (assistant + marketing director)

`OPENAI_API_KEY` — existing; spending capped via `AI_DAILY_SPEND_LIMIT_GBP`.

## FreeAgent (Priority 8 — incremental)

Existing `FREEAGENT_CLIENT_ID`, `FREEAGENT_CLIENT_SECRET`, `FREEAGENT_REDIRECT_URI` on the API URL (not the Next.js host).

## Railway layout (critical)

| Service | Must expose |
|---------|-------------|
| API (FastAPI) | `NEXT_PUBLIC_API_URL` target for the web app |
| Web (Next.js) | Marketing site + dashboard |
| Worker | Celery worker + beat |
| Redis | Broker for Celery and optional rate limits |

`NEXT_PUBLIC_API_URL` must point at the FastAPI service, not the Next.js hostname.