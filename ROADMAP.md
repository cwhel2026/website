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

## Phase 3 — Personal assistant (in progress)

| Item | Status |
|------|--------|
| Typed assistant tools + deterministic Q&A | Done |
| Audit log | Done |
| Approval centre + auto queue for complex quotes | Done |
| Morning/evening briefing generation | Done |
| Agent profiles, permissions, emergency stop | Done |
| Message templates + supervised outbound queue | Done |
| Telegram webhook (authorise admin IDs only) | Stub when not configured |
| OpenAI / LLM provider | Not connected |
| Automated scheduled briefings (Celery) | Not started |
| Live email/SMS send | Not started |

## Phase 4 — Regional marketing (in progress)

| Item | Status |
|------|--------|
| Diary-driven territory recommendations | Done |
| Regional campaigns + budget limits | Done |
| Meta/Google adapters (simulation only) | Done |
| Ad spend → approval centre | Done |
| Commercial leads + scoring | Done |
| Flyer campaigns + QR landing pages | Done |
| Attribution events | Done |
| Live Meta/Google API calls | Not implemented |
| Automated ad creative / posting | Not started |

## Phase 5 — Finance (in progress)

| Item | Status |
|------|--------|
| Invoices from quotations + payments | Done |
| Expenses + bank CSV import | Done |
| Tax reserve estimate (configurable rates) | Done |
| Job/territory profitability | Done |
| FreeAgent OAuth + live sync | Not verified / stub |
| Receipt OCR + S3 storage | Not started |
| Mettle direct API | Not available — document via FreeAgent |

## Phase 6 — Business intelligence

| Item | Status |
|------|--------|
| Stock items + low stock alerts | Done |
| Coating forecast from diary | Done |
| Analytics overview + regional | Done |
| Business Director task queue | Done |
| Celery workers / LLM director | Not started |
| Continuous learning models | Not started |

## Phase 7 — Production readiness

| Item | Status |
|------|--------|
| Security headers + request IDs | Done |
| Rate limits (quote, login, flyer) | Done |
| Production JWT / admin password gate | Done |
| `/ready` database probe | Done |
| Dockerfiles + prod compose | Done |
| Integration smoke test (CI with Postgres) | Done |
| Next.js CVE patch upgrade | Done (when lockfile updated) |
| HTTP-only cookie auth | Not started |
| Full E2E Playwright suite | Not started |
| Redis rate limits / Celery | Not started |

## Phase 8 — Expansion

Multi-van, multi-team, new territories.