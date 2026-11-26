# Railway — Stage 6 finance department (production)

Use one **API + worker** service (or combined Docker image) for finance. The **website-only** Next.js service cannot run Alembic, Celery, or receipt file storage alone.

## 1. Database migrations

On the API service:

```bash
cd apps/api && alembic upgrade head
```

Apply revisions **20251125_0004** through **20251125_0010** in order after merging PRs #20–#29.

For a single variable reference see **`RAILWAY_FINANCE_ENV.md`**.

## 2. Persistent receipt storage

Mount a Railway volume on the API container, e.g. `/data/finance-receipts`.

| Variable | Example | Purpose |
|----------|---------|---------|
| `FINANCE_RECEIPTS_DIR` | `/data/finance-receipts` | Primary receipt blobs |
| `FINANCE_RECEIPTS_BACKUP_DIR` | `/data/finance-receipts-backup` | Secondary copy on ingest (optional second volume) |

Without a volume, receipts live on ephemeral disk and are lost on redeploy.

## 3. Encryption key

**Reuse** your existing secret if already set — do not rotate without re-running FreeAgent OAuth.

If you need a new key only:

```bash
python apps/api/scripts/generate_finance_token_encryption_key.py
```

Set `FINANCE_TOKEN_ENCRYPTION_KEY` on the **API** service (and worker if separate).

## 4. FreeAgent OAuth

On API (+ worker if split):

| Variable | Value |
|----------|--------|
| `FREEAGENT_CLIENT_ID` | From https://dev.freeagent.com |
| `FREEAGENT_CLIENT_SECRET` | App secret |
| `FREEAGENT_REDIRECT_URI` | Must match app settings, e.g. `https://<api-host>/api/v1/finance/freeagent/callback` |

After deploy: Finance dashboard → Connect FreeAgent → **Full sync**.

## 5. Telegram receipts (split deploy)

**Website service:**

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Existing |
| `TELEGRAM_WEBHOOK_SECRET` | Existing |
| `TELEGRAM_ADMIN_IDS` | Existing |
| `API_INTERNAL_URL` | `https://<api-railway-url>` (no trailing slash) |
| `FINANCE_TELEGRAM_INGEST_KEY` | Random shared secret (match API) |

**API service:**

| Variable | Purpose |
|----------|---------|
| `FINANCE_TELEGRAM_INGEST_KEY` | Same as website |
| `OPENAI_API_KEY` | Optional receipt OCR |
| `FINANCE_RECEIPT_FREEAGENT_ATTACH` | `true` only after explanations exist in FreeAgent |
| `PUBLIC_DASHBOARD_BASE_URL` | Public site URL for report links in Telegram |

## 6. Celery worker

Same env as API plus:

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` / `CELERY_BROKER_URL` | Job queue |
| All finance/FreeAgent vars above | Sync + reports |

Start command (existing): `celery -A app.worker.celery_app worker --beat --loglevel=info`

Scheduled finance jobs: FreeAgent sync, categorisation, watchdog (07:00 UK), daily finance report (06:45 UK), weekly report (Sunday 08:00 UK).

## 7. Backup and recovery

- **Postgres:** Railway automated backups + `pg_dump` before major releases.
- **Receipts:** replicate `FINANCE_RECEIPTS_DIR` to `FINANCE_RECEIPTS_BACKUP_DIR` on each ingest; periodically copy volume snapshots off-platform.
- **FreeAgent:** remains authoritative — reconnect OAuth if tokens lost after key rotation.

## 8. Accountant user

Create a user with role `accountant` (migration 0008). They can access `/api/v1/finance/accountant/*` and CSV exports only.