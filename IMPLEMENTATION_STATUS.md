# Implementation status

Last updated: 2025-11-24 (stages 1–4 recovery).

Status legend: **Not started** · **Scaffolded** · **Implemented** · **Tested locally** · **Integration verified** · **Production verified** · **Blocked**

## Stage 4 (this run): FreeAgent, Alembic, rate limits

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