# Development roadmap

Aligned with the master specification phases.

## Phase 1 — Foundation

| Item | Status |
|------|--------|
| Monorepo, DB, territories, CRM, pricing, quotes, website, dashboard | Done (see PR #1) |

## Phase 2 — Regional operations (in progress)

| Item | Status |
|------|--------|
| Job + appointment models | Done |
| Two-stage workflow + seven-day monitoring | Done (core) |
| Scheduling proposals + conflict detection | Done (v1) |
| Weather simulation + suitability scores | Done (not live API) |
| Regional workload endpoint | Done |
| Calendar + field mobile UI | Done (shell) |
| OR-Tools / Google Calendar / live weather | Not started |
| PostGIS routing clusters | Not started |

**Acceptance**: Owner can create a job from a quotation, propose wash/coat slots with weather checks, view calendar and wash-pending queue, and use the field today list.

## Phase 3 — Personal assistant

AI assistant, Telegram, briefings, communications, approval centre.

## Phase 4 — Regional marketing

Ads adapters (supervised), commercial leads, flyers, attribution.

## Phase 5 — Finance

FreeAgent/Mettle verification, invoices, CSV fallback.

## Phase 6 — Business intelligence

Inventory, analytics, Business Director orchestration.

## Phase 7 — Production readiness

Security review, E2E tests, monitoring, deployment.

## Phase 8 — Expansion

Multi-van, multi-team, new territories.