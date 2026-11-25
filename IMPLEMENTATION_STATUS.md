# Implementation status

Last updated: 2025-11-25 (stage 6 Phase A — UK Ltd onboarding + FreeAgent sync).

Status legend: **Not started** · **Scaffolded** · **Implemented** · **Tested locally** · **Integration verified** · **Production verified** · **Blocked**

## Stage 6 Phase A (UK Ltd finance foundation)

| Feature | Status | Evidence / limits |
|---------|--------|-------------------|
| Company profile + onboarding wizard API | **Tested locally** | `routers/company.py`, `services/company/onboarding.py` |
| Company setup dashboard | **Implemented** | `dashboard/company-setup/page.tsx` |
| Token encryption at rest | **Tested locally** | `token_vault.py`, `test_stage6_finance_phase_a.py` |
| FreeAgent bank sync + audit | **Implemented** | `freeagent_sync.py`, migration **0004** |
| Scheduled FreeAgent sync | **Implemented** | `rmd.freeagent_sync_incremental` |
| Corporation tax planning stub | **Implemented** | `tax_engine/` — provisional rates only |
| Intelligent bookkeeping Phase B | **Tested locally** | PR stack — bookkeeping, Telegram receipts, Money hub |
| Phases C–F (PR stack #23–#26) | **Tested locally** | See `STAGE6_FINANCE.md` verification matrix |
| Stage 6.1 FreeAgent bills/reports/payroll read | **Tested locally** | PR stack #27, migration 0009, verification matrix |
| Stage 6 production sign-off | **Blocked** | Merge PRs #20→#27, `RAILWAY_STAGE6_FINANCE.md` |

## Stage 5 (in progress)

| Feature | Status | Evidence / limits |
|---------|--------|-------------------|
| Booking weather cache safety | **Tested locally** | `weather/service.py` rejects simulated/stale cache when `for_booking=True`; `test_weather_booking_safety.py` |
| Worker weather risk (no simulation for suitability) | **Implemented** | `appointment_weather_risk` sets `weather_suitable=None` when live fetch fails |
| HQ weather refresh reporting | **Implemented** | Simulation-only refresh marks job **failed** with explicit error |
| Public quotation API surface | **Tested locally** | `PublicQuotationOut`, sanitized `breakdown`, server-side travel distance |
| `GET /quotations/{id}` exposure | **Implemented** | Admin auth required |
| Legacy `POST /quotations/instant` | **Implemented** | Returns **410** for public clients |
| Telegram outbound `sendMessage` | **Implemented** | `services/telegram/client.py` |
| Telegram webhook delivery + dedupe | **Implemented** | `routers/telegram.py`, `telegram_processed_updates` |
| Notification outbox + Celery delivery | **Implemented** | `notification_outbox`, `rmd.deliver_notification_outbox` (migration **0003** required) |
| Telegram delivery in production | **Blocked** | Needs `TELEGRAM_*` env + migration + webhook registration (`STAGE5_CREDENTIALS.md`) |
| PWA web push, Meta/Google ads, AI write tools | **Not started** | See stage 5 brief |

## Stage 4: FreeAgent, Alembic, rate limits

| Feature | Status | Evidence / limits |
|---------|--------|-------------------|
| FreeAgent OAuth (authorize + callback) | **Tested locally** | `finance/freeagent_client.py`, `GET /finance/freeagent/authorize`, `/callback` |
| FreeAgent invoice sync (matched rows) | **Implemented** | `sync_invoices_from_freeagent`, `POST /finance/freeagent/sync` |
| Finance dashboard connect + sync UI | **Implemented** | `dashboard/finance/page.tsx` |
| Alembic revision 0002 (OAuth columns) | **Implemented** | `alembic/versions/20251124_0002_freeagent_oauth.py`, `MIGRATIONS.md` |
| Opt-out `create_all` when migrations managed | **Implemented** | `DATABASE_MIGRATIONS_MANAGED` in `main.py` |
| Redis-backed rate limits (optional) | **Implemented** | `RATE_LIMIT_STORAGE_REDIS` + `REDIS_URL` in `rate_limit.py` |
| FreeAgent live in production | **Blocked** | Owner registers app + sets Railway env + completes OAuth |

## Stage 3: Weather + background workers

| Feature | Status |
|---------|--------|
| Open-Meteo, Celery, job audit | **Production verified** (owner configured Redis + worker on Railway) |

## Stage 1–2

Public imagery audit (PR #12), quotations, AI orchestrator, marketing capacity — on `main`. See git history and prior rows in this file.

## Still open

| Area | Status |
|------|--------|
| Full Playwright production E2E suite | **Not started** |
| HTTP-only cookie auth | **Not started** |
| Imprinted concrete reference photo | **Pending asset** |
| Live Meta/Google ads | **Blocked** (credentials) |