# Remediation tracker

Baseline: [`docs/ARCHITECTURE_AUDIT_2026-11.md`](ARCHITECTURE_AUDIT_2026-11.md) (audit item numbers in
brackets). Updated at the end of every phase. Branch for Phase 1: `cursor/phase1-foundations-9428`.

## Status key

| Status | Meaning |
|--------|---------|
| **Verified (local)** | Fixed and proven by running it against real Postgres/Redis/browser on the dev VM |
| **Verified (CI)** | As above, and the proof runs in GitHub Actions on every push |
| **Awaiting deploy** | Code verified, but production has not received it yet, so production behaviour is unverified |
| **Owner action** | Needs a Railway/GitHub/credential step only the owner can do |
| **Open** | Not started (scheduled for a later phase) |

Nothing below is marked as working in production. Production still runs `main` (checked
26 Nov 2026 20:39 UTC: `/api/v1/ops/schema` → 404, `/api/v1/communications/templates` → 200 unauthenticated).

---

## Phase 1: Foundations

### Security

| ID | Issue | Priority | Depends on | Status | Verification |
|----|-------|----------|------------|--------|--------------|
| S1 | Meta webhook accepted unsigned/unprefixed posts [2] | P0 | — | Verified (CI) · Awaiting deploy | `app/security/webhooks.py`: 503 without `META_APP_SECRET`, 403 on missing/invalid `sha256=` signature. Also fixed: subscription check read `hub_mode` instead of Meta's `hub.mode`, so Meta could never verify the webhook. `test_webhook_security.py` (12) |
| S2 | Inbound-email webhook unauthenticated | P0 | — | Verified (CI) · Awaiting deploy | Requires `X-Webhook-Secret` = `EMAIL_INBOUND_WEBHOOK_SECRET`, constant-time compare; refused when unset |
| S3 | Public endpoints creating records / leaking data (`POST /crm/enquiries`, `GET /communications/templates`) | P0 | — | Verified (CI) · Awaiting deploy | Now admin-only. `test_route_auth_allowlist.py` fails CI if any new route is public without being added to a 27-entry allowlist |
| S4 | Attribution beacon unrate-limited [5] | P1 | — | Verified (CI) | 30/min per client IP. Rate-limit key uses the right-most `X-Forwarded-For` only when the peer is the local proxy (cannot be spoofed to evade limits) |
| S5 | JWT in `localStorage` [2] | P0 | — | Verified (CI) · Awaiting deploy | HttpOnly `sc_session` cookie (Secure in production, SameSite=Lax) + `sc_csrf` double-submit token bound to a JWT claim. Browser suite asserts the session cookie is HttpOnly, not readable by JS, and no token in localStorage. Legacy localStorage token is purged on load |
| S6 | CSRF once cookies are used [6] | P0 | S5 | Verified (CI) | Unsafe methods with cookie auth need `X-CSRF-Token` matching the claim; `test_session_security_integration.py` |
| S7 | OAuth tokens could fall back to plaintext [3] | P0 | — | Verified (CI) | `token_vault.py`: encryption requires `FINANCE_TOKEN_ENCRYPTION_KEY` ≥32 chars, no plaintext writes; legacy values readable once then re-encrypted; FreeAgent connect refused without key. `test_token_vault.py` (6) |
| S8 | Factory-default owner password only logged [4] | P1 | — | Verified (CI) · Awaiting deploy | Production refuses sign-in with a factory default (403 with fix instructions). `test_factory_password_refused.py`. **Risk:** if production still uses the default, the owner must set `DEFAULT_ADMIN_PASSWORD` in Railway and redeploy before signing in |
| S9 | API authentication/authorisation audit | P0 | — | Verified (CI) | Every route checked; assistant chat and FreeAgent authorise now admin-only; constant-time compares for Telegram/bookkeeping/owner-recovery keys; login timing equalised (no account enumeration). Auditor role is GET-only server-side |
| S10 | Ad launch bypassed approval (`launch-approved` accepted DRAFT) [12] | P0 | — | Verified (CI) | Approving/rejecting an `AD_SPEND` request now moves the campaign to APPROVED/DRAFT; launch requires APPROVED (409 otherwise). `test_campaign_approval_integration.py` |
| S11 | Outreach emails marked SENT without SMTP | P0 | — | Verified (CI) | Recorded as `not_sent_smtp_unconfigured`, API returns `live: false` |
| S12 | Owner password reset to env value on every boot (overrides recovery) | P2 | — | Open | Documented behaviour; env is the source of truth. Revisit in Phase 2 |
| S13 | Railway health check disabled (`healthcheckPath` empty) | P2 | D1 | Owner action | Recommend `/ready` once Phase 1 is deployed and stable (it now returns 503 when the schema is behind) |

### Database

| ID | Issue | Priority | Depends on | Status | Verification |
|----|-------|----------|------------|--------|--------------|
| D1 | Two schema authorities (`create_all` + optional Alembic) [7] | P0 | — | Verified (CI) · Awaiting deploy | `create_all` removed; `start.sh` and API Dockerfile always run `python -m app.schema.cli upgrade` and fail closed; `/ready` 503 when not at head |
| D2 | Old Alembic chain failed on an empty database (0002) | P0 | — | Verified (CI) | Revision 0001 loads a frozen baseline on empty DBs; CI test *empty database → head* |
| D3 | Models vs migrations drift | P0 | D1 | Verified (CI) | Revision 0017 reconciles additively; CI *model-drift guard* fails if models change without a migration |
| D4 | Safe path for the existing production DB | P0 | D1 | Verified (local + CI simulation) · Owner action | Legacy simulation (old models + `create_all` + seeds) upgraded with row counts preserved; dry run lists exact changes then rolls back. **Owner:** run `python -m app.schema.cli dry-run` in the Railway shell before deploying (see `MIGRATIONS.md`) |
| D5 | Marketing overview "Unable to load" — root cause | P0 | D1 | Verified (local) · Awaiting deploy | Three causes reproduced: (1) missing columns `marketing_budget_policies.meta_weekly_budget_gbp` etc. (`UndefinedColumnError`) because columns were added after `create_all` built the table; (2) invalid enum literal `"active"` in the Growth Fund committed-budget query; (3) `MissingGreenlet` after a rollback in the overview handler. All fixed; overview and Growth Fund return 200 on the upgraded legacy DB and in the browser suite |
| D6 | Marketing / Growth Fund tables exist in production | P0 | D4 | Owner action | Cannot be verified without production access. After deploy, `GET /api/v1/ops/schema` (auditor) or the System health page shows table counts and drift |
| D7 | Enum label case mismatch (0008 added lowercase `accountant`) | P1 | D3 | Verified (CI) | 0017 adds uppercase `ACCOUNTANT`/`AUDITOR`; reconcile aligns defaults |
| D8 | Non-blocking drift on legacy DB (extra column, 3 extra indexes, nullability) | P3 | D3 | Open | Reported by `/ops/schema` as `other_drift`; harmless, cleanup later |

### Workers

| ID | Issue | Priority | Depends on | Status | Verification |
|----|-------|----------|------------|--------|--------------|
| W1 | No worker/beat in production [8] | P0 | D1 | Owner action | Code and config ready: `apps/combined/worker.sh`, `apps/combined/railway.worker.toml`, `RAILWAY_WORKERS.md`. **Not operational until the worker service is created and a task shows Last success in production** |
| W2 | No retries / duplicate-run protection | P0 | — | Verified (CI) | `GuardedTask`: per-minute slot dedupe, overlap lock, 2 retries with backoff for transient errors. `test_worker_guard_integration.py` (3) |
| W3 | No visibility of task health | P0 | — | Verified (local + CI) | `scheduler_heartbeats`, `GET /api/v1/ops/workers`, System health page: last success, last failure, next run, recent failures. CI starts a real worker and waits for the heartbeat row |
| W4 | Async tasks failed on repeat runs ("attached to a different loop") | P0 | — | Verified (local) | Found by the new dashboard. Worker processes now use an unpooled async engine. Local worker: `deliver_notification_outbox` failing every other run before; repeated successes after |
| W5 | 14 of 15 schedules never executed anywhere | P1 | W1 | Open | Each shows **Never run** until it fires in production. Verify individually after W1 |

### Misleading functionality

| ID | Issue | Priority | Depends on | Status | Verification |
|----|-------|----------|------------|--------|--------------|
| M1 | Sample buttons write real rows [3] | P0 | — | Verified (CI) | Removed from expenses, commercial leads, advertising. Browser suite fails if "sample" buttons appear |
| M2 | NaN on tax centre and director pay [4] | P0 | — | Verified (CI) | Fields mapped to API shape; unknowns shown as "Unknown"/"Cannot be calculated yet". Browser suite fails on any `NaN`/`undefined` on 17 pages |
| M3 | API failures shown as empty data [5] | P0 | — | Verified (CI) | `useApi` + `LoadState` on rewritten pages; every remaining `.catch(() => set…([]))` (36 sites) now reports to a red banner naming the endpoint and status. Disconnected integrations show "Not connected" |
| M4 | Simulated advertising not clearly labelled | P0 | S10 | Verified (CI) | `SimulatedBadge` on campaign lists; launch response says "SIMULATED ONLY — nothing was sent … no money was spent" |
| M5 | Finance hub / home dashboard 500 (`/finance/insights/tasks`) | P0 | — | Verified (local + CI) | Found by the browser suite: watchdog crashed when the reserve is uncomputable. Now reports "Tax reserve cannot be calculated yet" |
| M6 | Google Ads dry-run mock / stubs [22] | P2 | — | Open | Phase 4 |

### Testing

| ID | Issue | Priority | Depends on | Status | Verification |
|----|-------|----------|------------|--------|--------------|
| T1 | No authenticated browser tests [6] | P0 | S5 | Verified (local) · CI job added | `e2e/authenticated/*`: real login, 17 pages × mobile + desktop, API checks; 47/47 pass locally against real Postgres + API + production Next build |
| T2 | Production tests must be non-destructive | P0 | T1 | Verified (local) | Browser guard aborts all non-GET except login/logout; auditor role is GET-only server-side; tests assert no page mutates on load |
| T3 | Restricted production test account | P0 | T1 | Owner action | `E2E_AUDITOR_EMAIL` / `E2E_AUDITOR_PASSWORD` on Railway, GitHub secrets `PROD_E2E_EMAIL`, `PROD_E2E_PASSWORD`, `PROD_BASE_URL`; manual workflow *Production read-only checks*. See `docs/E2E_TESTING.md` |
| T4 | Migration path tests | P0 | D2 | Verified (CI) | 4 tests: empty, legacy, drift guard, idempotency |

---

## Phase 2: Public quotation & customer journey

**Operational rule:** Do **not** mark the instant quotation system as operational until a full customer quote (provisional price + submit) is verified on production mobile after deploy.

### Critical (customer-facing)

| ID | Issue | Priority | Status | Verification |
|----|-------|----------|--------|--------------|
| Q1 | Instant quote shows **Internal Server Error** on Calculate estimate (iPhone, production) | **P0 CRITICAL** | **Fix deployed to production API · owner mobile verify pending** | Root cause: `MissingGreenlet` on `PricingProfile.rules` (PR #57). Post-deploy: `POST …/quotations/provisional` with PR1 2AA → **200** + `total_inc_vat_gbp` (~1177.15 for 40 m² test). **Not marked operational** until full iPhone wizard (Calculate + submit) confirmed. |
| Q2 | Marketing slug vs catalogue slug (Service not found) | P0 | Verified (CI) · Awaiting deploy | Fixed on `main` via service alias map (`tarmac-restoration` → `tarmac-driveway-restoration`). |

### Phase 2 workstream (in progress)

| ID | Requirement | Status |
|----|-------------|--------|
| Q3 | Reproduce full public workflow; identify endpoint + exception | **Done (local)** | Endpoint: `POST /api/v1/quotations/provisional`. Exception: `MissingGreenlet` on pricing rules load. |
| Q4 | Migrations, pricing profile/rules, postcode lookup, travel distance | **Checked** | Schema at head; seeds provide pricing profile + rules. Travel uses postcodes.io + Preston base coords from `scheduling_settings` (operational, not advertised as HQ). Geocode errors now return 503 JSON instead of opaque 500. |
| Q5 | Genuine backend calculations in tests (no mocked totals) | **In CI** | `test_quotation_provisional_integration.py` + Playwright `e2e/public-quote-real.spec.ts` (mobile). |
| Q6 | Failed requests must not lose customer-entered data | **Done** | Quote wizard persists to `sessionStorage`; errors state details are saved. |
| Q7 | Quotation independent of marketing/accounting integrations | **Verified** | Provisional path uses only services, territories, pricing profile, postcodes.io. |
| Q8 | Mobile journey end-to-end test | **In CI** | `public-quote-mobile` Playwright project. |
| Q9 | Quotation progress bar overflow on mobile | **Fixed** | Step pills use responsive grid (4 cols mobile / 7 desktop) instead of horizontal scroll. |
| Q10 | Replace Revive My Drive → SurfaceCoat (public site) | **Done (web)** | Header, footer, layout metadata, service areas, commercial/privacy/media copy + Telegram-lite web routes updated. API seed emails / legacy domains may remain in backend until Phase 3. |
| Q11 | Coverage copy: Lancashire, GM, Merseyside, Cheshire, Cumbria, W Yorkshire; Preston as travel base only | **Done** | `public-brand.ts` + service-areas page. |
| Q12 | **Future (not implemented):** customer photo upload + AI driveway condition assessment | **Recorded** | Enhancement only — no code in this phase. |

### Future enhancements (explicitly not built in Phase 2)

| ID | Idea | Notes |
|----|------|-------|
| F1 | Photo upload on quote flow | Owner-supplied images stored securely; no AI spend. |
| F2 | AI-assisted condition grading from photos | Feeds *provisional* estimate hints only; must not auto-book or charge; needs consent + cost cap. |

---

## Later phases (not started; listed for dependency tracking)

| ID | Issue (audit ref) | Phase | Depends on |
|----|-------------------|-------|------------|
| L1 | One Telegram implementation (FastAPI); remove Next.js handlers [9] | 2 | — |
| L2 | Campaign/UTM keys on Enquiry → Quote → Job → Invoice [11] | 2 | D1 |
| L3 | Quote acceptance + job creation [12] | 2 | L2 |
| L4 | Job completion → FreeAgent invoice [13] | 2 | L3 |
| L5 | Bank ↔ invoice matching; Growth Fund inputs [14] | 3 | L4, W1 |
| L6 | Per-campaign profitability, Meta CAPI [15–16] | 4 | L5 |
| L7 | Consolidate marketing and finance surfaces [17–18] | 5 | — |
| L8 | Customer timeline [19] | 5 | L2 |
| L9 | Responsive tables → cards everywhere; restyle legacy pages [20] | 5 | — |
| L10 | GET endpoints that write (tax reserve snapshots) | 3 | — |
| L11 | Hardcoded pricing fallbacks / scheduling coordinates | 2 | — |
