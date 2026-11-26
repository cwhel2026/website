# Railway — consolidated finance environment (Stage 6.2)

One reference for **every** finance-related variable. **Reuse existing secrets** in Railway — do not rotate without a deliberate recovery plan.

## Service placement

| Service | Role |
|---------|------|
| **API** | Postgres, Alembic, FreeAgent OAuth, receipt files on volume, finance REST |
| **Worker** | Same env as API + Celery beat — **must** share `FINANCE_RECEIPTS_DIR` volume with API if workers process receipts |
| **Website (Next.js)** | Forwards Telegram photos to API — **no** receipt volume |

Receipt blobs are **never** on the website container.

---

## Mandatory (production finance)

| Variable | Service | Format / notes |
|----------|---------|----------------|
| `DATABASE_URL` | API, Worker | `postgresql+asyncpg://…` (API); worker uses sync URL via existing app config |
| `FINANCE_TOKEN_ENCRYPTION_KEY` | API, Worker | Fernet key from `python apps/api/scripts/generate_finance_token_encryption_key.py` |
| `JWT_SECRET` | API, Website | Strong random string; must not be default in `production` |
| `REDIS_URL` or `CELERY_BROKER_URL` | Worker | `redis://…` |
| `FREEAGENT_CLIENT_ID` | API, Worker | OAuth app id |
| `FREEAGENT_CLIENT_SECRET` | API, Worker | OAuth secret |
| `FREEAGENT_REDIRECT_URI` | API | Must match FreeAgent app, e.g. `https://<api-host>/api/v1/finance/freeagent/callback` |
| `FINANCE_RECEIPTS_DIR` | API, Worker | Absolute path on **mounted volume**, e.g. `/data/finance-receipts` |
| `FINANCE_TELEGRAM_INGEST_KEY` | API **and** Website | Shared random string for receipt forward auth |
| `API_INTERNAL_URL` | Website | `https://<api-host>` (no trailing slash) |
| `TELEGRAM_BOT_TOKEN` | API, Website | Existing bot |
| `TELEGRAM_WEBHOOK_SECRET` | Website | Webhook validation |
| `TELEGRAM_ADMIN_IDS` | API, Website | Comma-separated numeric Telegram user ids |
| `PUBLIC_DASHBOARD_BASE_URL` | API, Worker | Public site URL for Telegram report links |

---

## Optional (feature flags & quality)

| Variable | Service | Default | Purpose |
|----------|---------|---------|---------|
| `FINANCE_RECEIPTS_BACKUP_DIR` | API, Worker | — | Second volume path; copies on ingest |
| `FINANCE_RECEIPT_FREEAGENT_ATTACH` | API, Worker | `false` | PUT receipt to bank **explanation** after approval |
| `FINANCE_RECEIPT_FREEAGENT_EXPENSE` | API, Worker | `false` | POST **personal** director expenses with attachment |
| `FREEAGENT_DEFAULT_EXPENSE_CATEGORY_URL` | API, Worker | — | Override if category cache empty |
| `FREEAGENT_API_BASE` | API | `https://api.freeagent.com` | Sandbox base if testing |
| `OPENAI_API_KEY` | API | — | Receipt vision OCR |
| `OPENAI_MODEL` | API | `gpt-4o-mini` | OCR model |
| `PUBLIC_API_BASE_URL` | API | — | Fallback link base if dashboard URL unset |
| `ENVIRONMENT` | All | `production` | Enables security audit checks |

---

## Celery schedules (Europe/London)

| Task | Schedule |
|------|-----------|
| FreeAgent sync | 05:20 daily |
| Bookkeeping categorise | Every 4h |
| Financial watchdog | 07:00 daily |
| Finance report daily | 06:45 daily |
| Finance report weekly | Sun 08:00 |
| Finance report monthly | 1st 09:00 |
| Finance report annual | 1st 09:30 (runs on accounting year-end day from company profile) |
| Finance task centre | Mon 08:15 |
| Notification outbox | Every 2 min |

Worker start: `celery -A app.worker.celery_app worker --beat --loglevel=info`

---

## Backups

1. Railway Postgres backups + manual `pg_dump` before migrations.
2. Receipt volume: `FINANCE_RECEIPTS_BACKUP_DIR` on ingest + periodic off-platform copy.
3. FreeAgent remains authoritative if local volume is lost — re-attach from Telegram only where duplicates allow.

---

## Verification API

`GET /api/v1/finance/insights/security-audit` (admin) returns configuration evidence — **not** a claim of live production verification until the owner completes checklist and signs off in `STAGE6_VERIFICATION_MATRIX.md`.