# Implementation status

Last updated: 2025-11-24 (Phase 4 agent run).

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

**Test result (local)**: `22 passed` API pytest (2025-11-24).

## Partial / scaffold

| Item | Notes |
|------|-------|
| Alembic | Initial placeholder revision; dev uses `create_all` on startup |
| PostGIS geometry columns | Not yet on models (postcode/town resolution only) |
| Address autocomplete | Not integrated — provider TBD |
| AI photo assessment | Not built |
| Dashboard overview metrics | Empty until real data; no fabricated stats |

## Not started (remaining Phases 2–8)

OR-Tools, Google Calendar, live weather providers, Telegram, marketing APIs, FreeAgent, Mettle, inventory, AI agents, field photo uploads and offline queue, E2E DB tests, production deploy.

## Known defects / tech debt

- Next.js 15.1.0 has known security advisory — upgrade before production.
- JWT in `localStorage` — migrate to secure cookies.
- Enum types duplicated across SQLAlchemy models may need Alembic autogenerate cleanup.
- Docker not available in some cloud agent VMs — CI validates builds instead.

## Required credentials (none verified live)

See `INTEGRATIONS.md`.