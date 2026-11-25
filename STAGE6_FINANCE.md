# Stage 6 — UK Ltd financial platform

Architecture: **Mettle → FreeAgent → Revive AI Finance Director**. FreeAgent is authoritative; this platform adds onboarding, sync audit, planning tax constants, and (later phases) remuneration, receipts, and watchdog alerts.

## Phase A (this PR) — implemented

| Area | Status | Notes |
|------|--------|-------|
| Company profile + onboarding checklist | **Implemented** | `GET/PUT /api/v1/company/profile`, dashboard **Company setup** |
| Encrypted OAuth tokens | **Implemented** | `FINANCE_TOKEN_ENCRYPTION_KEY` or derived from `JWT_SECRET` |
| FreeAgent bank transaction import | **Implemented** | Paginated `/v2/bank_accounts` + `/bank_transactions`; duplicate skip |
| Invoice sync (existing) | **Implemented** | Matched local invoice rows only |
| Full sync endpoint | **Implemented** | `POST /finance/freeagent/sync/full` |
| Sync audit | **Implemented** | `finance_sync_runs` table |
| Scheduled sync | **Implemented** | Celery `rmd.freeagent_sync_incremental` (05:20 UK) |
| Corporation tax planning stub | **Implemented** | `GET /finance/tax/corporation-estimate` — **provisional**, no marginal relief |
| Alembic 0004 | **Implemented** | Company + sync tables |

## Phase B–F — not in this PR

Intelligent bookkeeping, Telegram receipts, versioned tax engine (VAT, PAYE, dividends), remuneration optimiser, director's loan, cash flow, job profitability, accountant role, financial dashboard sections, automated reports.

## Credentials / env

| Variable | Required | Purpose |
|----------|----------|---------|
| `FREEAGENT_CLIENT_ID` | For OAuth | FreeAgent app |
| `FREEAGENT_CLIENT_SECRET` | For OAuth | |
| `FREEAGENT_REDIRECT_URI` | For OAuth | Must match FreeAgent app settings |
| `FINANCE_TOKEN_ENCRYPTION_KEY` | Recommended in production | Fernet encryption for stored tokens |
| `DATABASE_MIGRATIONS_MANAGED` | Production | Run Alembic **0004** before deploy |
| FastAPI service | Required | Finance API not available on web-only Railway deploy |

## FreeAgent API — verified in code

| Endpoint | Use |
|----------|-----|
| OAuth authorize + token | Connection |
| `GET /v2/company` | Organisation name |
| `GET /v2/invoices` | Invoice sync |
| `GET /v2/bank_accounts` | Bank list |
| `GET /v2/bank_transactions` | Paginated import |

Not yet integrated: bills, expenses, attachments, contacts (enums reserved in `finance_sync_runs`).

## Professional review required

- Initial remuneration strategy (salary vs dividends)
- VAT scheme selection and registration timing
- Corporation tax returns and filings
- Any figure marked `requires_accountant_review: true`

## Owner setup

1. Apply migration `20251125_0004`.
2. Set FreeAgent OAuth env on the **API** service (or use combined Docker image).
3. Open **Company setup** and enter Companies House number and dates.
4. Connect FreeAgent from **Finance**, then run **Full sync**.
5. Set `FINANCE_TOKEN_ENCRYPTION_KEY` before reconnecting if tokens were stored unencrypted in dev.