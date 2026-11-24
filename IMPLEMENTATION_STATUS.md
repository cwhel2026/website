# Implementation status

Last updated: 2025-11-24 (Phase 7 agent run).

## Completed and tested

| Capability | Evidence |
|------------|----------|
| Postcode outward district parsing | `apps/api/tests/test_territory_lookup.py` (3 tests) |
| Pricing engine (minimum job, condition, margin) | `apps/api/tests/test_pricing_engine.py` (4 tests) |
| Territory A–I seed data | `apps/api/app/seeds/bootstrap.py` |
| Services catalogue seed | Same |
| Default pricing profile rules | Same |
| REST: territories, services, CRM, quotations, auth | `apps/api/app/routers/*` |
| Public Next.js pages | `apps/web/src/app/(site)/*` |
| Dashboard pages | `apps/web/src/app/dashboard/*` |

| Phase 2 jobs, appointments, scheduling, weather simulation | API + dashboard pages |
| Seven-day coating risk assessment | `two_stage_workflow.py` + tests |
| Regional workload API | `/regional/workload` |

| Personal assistant (tool-backed chat) | `/assistant/chat` + dashboard |
| Approval centre | Quotations + outbound messages |
| Briefings | `/briefings/generate/*` |
| Agents / emergency stop | `/automations/*` |

| Diary-driven marketing recommendations | `/marketing/recommendations` |
| Regional campaigns, flyers, commercial leads | `/marketing/*` |
| QR attribution landing | `/c/[slug]` |

| Invoices, expenses, CSV bank import | `/finance/*` |
| Tax reserve estimate | Configurable tax year settings |
| Territory/job profitability | Quotation contribution − expenses |

| Stock + coating forecast + low stock | `/inventory/*` |
| Analytics KPI snapshot | `/analytics/overview` |
| Business Director scan + task queue | `/business-director/*` |
| Dashboard: analytics, inventory, system health | `apps/web/src/app/dashboard/*` |

| Production gates (JWT/admin password) | `app/security/startup.py` |
| Rate limits + security headers | `slowapi` + middleware |
| `/health` + `/ready` | `app/routers/health.py` |
| Docker images + prod compose | `apps/*/Dockerfile`, `docker-compose.prod.yml` |

**Test result (local)**: 31 passed, 1 skipped (integration); CI runs Postgres smoke job.

## Partial / scaffold

| Item | Notes |
|------|-------|
| Alembic | Initial placeholder revision; dev uses `create_all` on startup |
| PostGIS geometry columns | Not yet on models (postcode/town resolution only) |
| Address autocomplete | Not integrated — provider TBD |
| AI photo assessment | Not built |
| Dashboard overview metrics | Empty until real data; no fabricated stats |

## Not started (remaining Phases 2–8)

OR-Tools, Google Calendar, live weather providers, Telegram, marketing APIs, FreeAgent, Mettle, Celery agent workers, field photo uploads and offline queue, E2E DB tests, production deploy.

## Known defects / tech debt

- Next.js 15.1.0 has known security advisory — upgrade before production.
- JWT in `localStorage` — migrate to secure cookies.
- Enum types duplicated across SQLAlchemy models may need Alembic autogenerate cleanup.
- Docker not available in some cloud agent VMs — CI validates builds instead.

## Required credentials (none verified live)

See `INTEGRATIONS.md`.