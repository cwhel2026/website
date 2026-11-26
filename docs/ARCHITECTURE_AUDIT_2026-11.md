# SurfaceCoat — Independent Architecture Audit (26 Nov 2026)

Scope: whole repository at `main` @ merge of PR #51. Read-only audit; no feature work.

## How each finding was verified

| Tag | Meaning |
|-----|---------|
| **[T]** | Tested by running it: unit tests, live production HTTP, or a browser screenshot |
| **[C]** | Confirmed by reading the code (file:line given) |
| **[U]** | Unverified: depends on Railway configuration or credentials I cannot see |

What was actually run:

- Backend unit tests: **106 passed, 5 skipped** in 3.8 s **[T]**. These are mostly pure-function tests. Only one integration test touches a real database (CI only).
- Production: `/`, `/api/live`, `/health`, `/api/ready` all return 200. The database check passes. A bad login returns 401 **[T]**.
- **Not tested: any signed-in production page.** I have no production credentials, so I cannot claim the marketing overview, dashboard KPIs or any form works in production.
- Signed-in portal layout at 390 px, with the API stubbed in the browser: 7 routes, no horizontal overflow, two visual regressions found (§13) **[T]**.

**Correction to earlier work:** the "mobile screenshots" committed in PR #50 (`apps/web/e2e/screenshots/portal-*.png`) are byte-identical. Every one is the login page, because the test never authenticated. They prove nothing about the signed-in portal.

---

## 1. Executive summary

SurfaceCoat is **not yet one business operating system**. It is a large set of reasonably well-built department modules: about 21.5k lines of Python, 62 Next.js pages and 16 Alembic migrations. They share a database but are joined at only a few points.

The lead-to-cash-to-marketing loop you described breaks at **six** hand-offs:

```
Meta lead / web quote → CRM enquiry        WORKS (attribution is weak)
Enquiry → quotation                         WORKS for the web quote; Meta leads get no quote
Quotation → ACCEPTED                        MISSING  (no code ever sets status=accepted)
Accepted quote → job/booking                MANUAL   (admin button, no accepted check)
Scheduling: location + weather + clashes    PARTIAL  (real weather; location often a hardcoded default)
Job → COMPLETED                             MISSING  (no code ever sets JobStatus.COMPLETED)
Completed job → invoice                     MANUAL   (from the quotation only; job_id never passed)
Payment ↔ bank reconciliation               PARTIAL  (FreeAgent import works; invoice matching never set)
Payment → 5% Growth Fund                    PARTIAL  (logic correct; usually skipped because nothing is reconciled)
Revenue → originating campaign              MISSING  (no campaign_id on enquiry/job/invoice)
AI director learns from attributed profit   MISSING  (uses spend, engagement and aggregate totals only)
```

**Background automation does not run in production.** Seventeen scheduled Celery tasks (weather refresh, Telegram notification delivery, morning briefing, FreeAgent sync and the Growth Fund allocation that follows it, finance reports, watchdog) are defined. But only local `docker-compose.yml` starts a worker. The Railway combined container starts Next.js and uvicorn only. **[C]** `apps/combined/start.sh`; `docker-compose.yml:23-27`. **[U]** unless you run a separate Railway worker service.

**Strengths worth keeping:** an honest FreeAgent OAuth client with real HTTP calls; tax rules with GOV.UK sources and "provisional" labels; a real Open-Meteo weather provider with a simulation guard for bookings; server-side marketing spend caps; a Growth Fund ledger with dedupe keys and no fake transfers; working API routing (every dashboard fetch matches a backend route); a stable production deploy.

---

## 2. Department scorecard

Scores out of 10: **F** functionality, **I** integration, **R** reliability, **S** security, **U** usability.

| Department | F | I | R | S | U | One-line verdict |
|---|---|---|---|---|---|---|
| Platform / Railway deploy | 7 | 6 | 6 | 6 | — | Stable now; no worker; split schema authority |
| Database & migrations | 6 | 5 | 4 | 6 | — | `create_all` and Alembic both claim the schema; weak FKs on attribution |
| Auth & security | 6 | — | 6 | 5 | 6 | bcrypt + JWT fine; localStorage token; webhook bypass; plaintext token fallback |
| CRM & customers | 5 | 3 | 5 | 6 | 4 | Enquiries are created; commercial leads bypass the CRM; no pipeline actions |
| Quoting & pricing | 7 | 4 | 6 | 7 | 5 | DB-driven pricing works; hardcoded fallbacks; no acceptance step |
| Scheduling & weather | 6 | 4 | 5 | 7 | 4 | Real weather + clash checks; jobs lose property location; no completion step |
| Accounting & banking | 6 | 5 | 5 | 6 | 5 | Real FreeAgent; two invoice sources of truth; no bank↔invoice matching |
| Growth Fund | 6 | 3 | 5 | 7 | 6 | Correct and honest maths; starved of reconciled inputs; no campaign link |
| Company / tax / director pay | 6 | 5 | 5 | 6 | 3 | Good rules engine; **two UI pages read the wrong response fields** (NaN) |
| Meta advertising | 4 | 4 | 5 | 4 | 4 | Real reads/publish/pause; dashboard launch is simulated; CAPI never called |
| Google Ads / GA4 / GSC / GBP | 1 | 1 | — | — | 2 | Stubs or credential checks only |
| Marketing intelligence / AI director | 5 | 3 | 5 | 6 | 4 | Uses real data, but not attributed revenue or profit |
| AI assistant | 6 | 6 | 6 | 6 | 5 | Read-mostly tools over real data; spend limit exists |
| Telegram | 5 | 3 | 5 | 6 | 5 | **Two implementations**; production webhook served by the simpler Next.js one |
| Background workers | 7 (code) | 2 | 1 | — | — | Well-written tasks that do not run in production |
| Mobile UX / portal | 5 | — | 5 | — | 4 | New shell works; ~29 pages unreadable inside it; cookie banner covers the nav |

---

## 3. Platform, deployment and architecture

**Works [T]:** a single Railway combined container. Next.js listens on `$PORT`; FastAPI runs on `127.0.0.1:8000`; Next.js rewrites `/api/v1/*`, `/health` and `/ready` to it (`apps/web/next.config.ts`). Liveness and readiness pass in production.

**Issues**

- **No worker or beat process in production [C].** All scheduled work is dead (see §1).
- **Two schema authorities [C].** `app/main.py:78-80` runs `Base.metadata.create_all` unless `DATABASE_MIGRATIONS_MANAGED=true`. `start.sh` runs `alembic upgrade head` only if a flag is set. Alembic `0001` is a no-op baseline. So in production, tables can come from `create_all`, which never alters existing columns, while later revisions add columns. Whether production Postgres matches the models is **[U]**. This is the most likely cause of the "Unable to load marketing overview" error you saw: missing tables from 0015/0016 when Alembic has not run.
- **Bootstrap failures are logged, not surfaced [C]** (`main.py:84-85`). `/ready` reports "database ok" even if seeding or migrations failed.
- **Documentation sprawl:** 40 root-level `*.md` files, many of them stage reports (`STAGE7_*`, `RAILWAY_FIX_NOW.md`, `IMPLEMENTATION_STATUS.md`) that overlap and are now partly stale. They should be reduced to README, ARCHITECTURE, DEPLOYMENT, RUNBOOK and BUSINESS_RULES.

## 4. Database

- Core relationships exist: Quotation→Enquiry FK (`quotation.py:51-53`); Job→Quotation.
- **Attribution is not relational [C].** `AttributionEvent.customer_id` and `enquiry_id` are plain UUIDs, not FKs (`models/marketing.py:161-162`). `Customer.campaign` is free text (`models/crm.py:45`). There is no `campaign_id` on Enquiry, Job or Invoice.
- **Duplicate concepts [C]:** `CommercialLead` vs `CommercialProspect`; CRM `Enquiry` vs `MarketingMetaLead` vs `CommercialLead`; `AttributionEvent` vs `Customer.source`/`campaign` strings.
- `GrowthFundLedger.campaign_id` exists but is never populated (`marketing_growth_fund.py:57`).

## 5. Authentication and security

**Works [C/T]:** bcrypt hashing; JWT with an 8-hour expiry; production refuses to start with a default or short JWT secret (`security/startup.py`); role gates for admin, owner and accountant; slowapi rate limits on login, recovery, public quote and commercial endpoints; CORS allow-list; security-headers middleware; Telegram webhook secret check (tested).

**Issues (priority order)**

1. **Meta lead webhook signature bypass [C]** (`routers/marketing_webhooks.py:27-33`). If `META_APP_SECRET` is unset, unsigned posts are accepted. If it is set, a header that is present but does not start with `sha256=` skips verification. Either way, anyone can inject fake leads into the CRM.
2. **The JWT lives in `localStorage`** (`lib/auth-client.ts`), so any XSS on the shared origin (public site + portal) can steal an 8-hour admin token. Recommendation: an httpOnly, SameSite=Strict cookie set by the API through the same-origin proxy.
3. **OAuth token encryption can fall back to plaintext** when key material is under 16 characters (`services/finance/token_vault.py:23-28`).
4. A default admin password is only logged as CRITICAL, not refused (`security/startup.py`).
5. The unauthenticated `/marketing/attribution/track` beacon has no rate limit (`routers/marketing.py:652`).
6. No CSRF exposure today (bearer header), but this becomes relevant when moving to cookies.

## 6. CRM and customers

- Meta webhook → Customer + Enquiry + AttributionEvent + MarketingMetaLead (`meta_leads_service.py:21-54`) **[C]**. It never fetches lead details from the Graph API, so contacts get placeholder `@leads.invalid` emails and no phone number.
- The web quote creates Customer, Property, Enquiry and Quotation (`quotation_persist.py:107-146`) **[C]**.
- **The commercial enquiry form writes only a `CommercialLead`; no CRM record [C]** (`routers/public.py:50-82`).
- The UI has customer and enquiry lists only. There are no pipeline stages you can act on, no notes or tasks, and no single customer timeline linking quotes, jobs, invoices and messages.
- The customers table overflows on mobile.

## 7. Quoting and pricing

- The pricing engine is DB-driven (`PricingProfile`/`PricingRule`), but falls back to hardcoded rates (for example £18/m², labour £159, `pricing_engine.py:62-137`) **[C]**. These fallbacks should be removed or loudly flagged when used.
- **There is no customer or admin "accept quote" action anywhere; `QuotationStatus.ACCEPTED` is never written [C].** The analytics "quotes accepted" and conversion rate are therefore always 0.
- Approvals move quotes only to SENT or REJECTED (`routers/approvals.py:70-104`).

## 8. Scheduling and weather

- Clash detection (double booking + owner blocks) is enforced on appointment create (`scheduling_engine.py:42-67`, `jobs.py:238-243`) **[C]**.
- Open-Meteo is the live provider; simulated weather is refused for bookings unless explicitly allowed (`weather/service.py:29-56`) **[C]**; unit-tested **[T]**.
- `job_from_quotation` does not copy `property_id`, so slot proposals fall back to **hardcoded coordinates 53.65, -2.95** (`jobs.py:164-183`) **[C]**.
- **There is no "coating complete / job complete" endpoint;** jobs can never reach COMPLETED **[C]**.
- The weather-risk alerts rely on the Celery tasks that do not run (§1).

## 9. Accounting and banking

- FreeAgent: real OAuth plus invoices, bank accounts and transactions, bills, expenses, P&L, balance sheet and payroll (`freeagent_client.py:119-297`) **[C]**. The disconnected state is shown honestly.
- Mettle has no API. The bank feed comes via FreeAgent or CSV import, and this is documented correctly.
- **Two invoice sources of truth [C].** Local `Invoice` is created from quotations. FreeAgent sync updates only local rows that already have a `freeagent_id`. Local invoices are never pushed to FreeAgent. Recommendation: **FreeAgent is the ledger; the app creates invoices *in* FreeAgent and mirrors them.**
- **`BankTransaction.matched_invoice_id` is never set [C],** so payments are never reconciled to invoices automatically.
- Silent failures: Growth Fund errors are swallowed during sync (`freeagent_sync.py:150-151`); `except Exception: pass` on invoice totals (`freeagent_adapter.py:202-203`); pagination stops on any HTTP error.
- UI: the **"Add sample expense"** button posts a real £45.50 expense (`expenses/page.tsx:20-36`). Finance, finance-hub, invoices and expenses overlap.

## 10. Growth Fund

- The maths is correct and honest: 5% of eligible bank inflows, ex-VAT when invoice-matched, refunds reversed, exclusions, dedupe keys, "virtual reserve, not a bank balance" (`growth_fund.py:147-280`) **[C]**; unit-tested **[T]**.
- **Inputs are starved [C].** Eligibility requires `is_reconciled` or `matched_invoice_id` (`growth_fund_eligibility.py:28-29`). Matching is never set, and the daily sync does not run in production. Net effect: the fund only moves when you press "process allocations" after reconciling manually.
- No campaign attribution on allocations.

## 11. Company, tax and director pay

- The rules packs for 2025/26 and 2026/27 have sources and verified dates, and are labelled "planning only" (`tax_engine/rules_uk_ltd.py:48-138`) **[C]**.
- **UI response-shape bugs [C]:** the tax centre reads flat `corporation_tax_gbp` but the API returns `corporation_tax.amount_gbp`, so the page shows NaN. Director pay reads `personal.salary_gross_gbp` but the API returns it on `recommended`.

## 12. Marketing

**Meta [C]:** real Graph calls for account insights, page posts, IG media, post insights, feed publishing, campaign create (PAUSED) and pause-all. However:

- The dashboard "launch" path (`ad_adapters.launch_campaign`) simulates or refuses; it never calls Meta (`ad_adapters.py:55-77`).
- `create_paused_search_campaign` is unused.
- The **Conversions API sender exists but is never called,** so Meta never learns which leads became paying jobs. This is central to your "AI improves future ads" goal.
- `launch-approved` does not verify the ApprovalRequest status (`routers/marketing.py:463-465`).

**Spend safety [C]:** server-side daily, weekly, platform and Growth Fund caps, with live spend off by default (`budget_controls.py:46-94`). Good.

**Google Ads, GA4, GSC and GBP:** stubs. Google Ads uses the refresh token as a bearer token, which would fail if live.

**Intelligence:** uses real appointments, territories and synced post metrics. No random or fake data found. But ROAS is "all paid invoices ÷ all campaign spend" (`attribution_journey.py:46-82`), not per campaign.

**Duplication:** `/dashboard/marketing/*` (director) vs `/marketing-hub` vs `/advertising` vs `/content-studio` vs `/content-calendar` vs `/marketing-integrations`; two Google Ads clients; two profitability endpoints. The `/marketing/leads` page is a static link only.

## 13. Portal UX and mobile (tested in a browser at 390 px, API stubbed)

- New shell: compact header, no horizontal overflow on the 7 routes tested **[T]**.
- **Regression from PR #50 [T]:** about 29 legacy pages use `text-emerald-950`, `text-asphalt` or `text-slate-9xx` headings, which are now **dark on charcoal and nearly invisible** (screenshots: `audit-390_dashboard_quotations.png`, `audit-390_dashboard_finance-hub.png`).
- **The public-site cookie banner renders inside the portal and covers the bottom navigation [T]** (root `layout.tsx` mounts `ConsentBanner` globally).
- The browser tab title in the portal is still "Revive My Drive"; the public site is still entirely Revive My Drive.
- Quotations, customers and invoices tables have no `overflow-x-auto` wrapper.
- Sample-data buttons: "Create sample" campaign, "Add sample lead", "Add sample expense".
- Swallowed errors: most pages use `.catch(() => setX([]))`, so an API failure looks identical to "no data".

## 14. AI assistant and Telegram

- Assistant: an OpenAI/Claude orchestrator with a daily £ spend cap and read-mostly tools over real data (jobs, approvals, analytics, marketing); the one write tool is emergency pause **[C]**. It has no access to finance, CRM write, quote creation or scheduling actions.
- **Telegram is duplicated [C].** FastAPI has `routers/telegram.py` with the full assistant. Next.js has `app/api/v1/telegram/{webhook,status,register-webhook}` with `lib/telegram/assistant-lite.ts`. In the combined deploy, Next.js serves its own route handlers before applying the `/api/v1/*` rewrite, so **the production Telegram webhook is answered by the lightweight Next.js version, not the full FastAPI assistant.** Outbound notifications rely on the worker that does not run.

## 15. Placeholder, simulated and hardcoded data inventory

| Item | Location | Severity |
|---|---|---|
| Sample expense / lead / campaign buttons write real rows | expenses, commercial-leads, advertising pages | High |
| Hardcoded pricing fallbacks | `pricing_engine.py:62-137` | Medium |
| Hardcoded scheduling coordinates | `jobs.py:164-183` | Medium |
| Meta placeholder emails `@leads.invalid` | `meta_leads_service.py` | Medium |
| Default Growth Fund £600 launch contribution / "£150/week" copy | `growth_fund.py:34,107` | Low (documented) |
| `/dashboard/website` static "Scaffolded/Not started" checklist | `website/page.tsx` | Low |
| Ad launch simulation path | `ad_adapters.py:55-77` | Medium (labelled) |

---

## 16. Prioritised remediation roadmap

Ordered by risk to daily use, then by how much of the operating-system loop each item unblocks. Each item is tightly scoped and reuses existing code; **no rewrite is justified.**

### P0: Stabilise and stop misleading (small, contained)

1. **Fix the PR #50 regressions:** make legacy page content readable inside the dark shell; hide the cookie banner on `/dashboard/*`; portal page title "SurfaceCoat".
2. **Close the Meta webhook bypass:** require a valid `sha256=` signature always in production; refuse if the secret is unset.
3. **Remove "sample" buttons** that write real records.
4. **Fix tax-centre and director-pay field mapping** (NaN).
5. **Make failures visible:** a shared `useApi` hook that shows the HTTP status instead of an empty list; remove `except: pass` in finance sync.
6. **Real authenticated Playwright suite** against a seeded test database (CI) and a read-only production smoke with a dedicated test user.

### P1: Make production run the business (platform)

7. **Single schema authority:** Alembic only. Generate a true baseline from the models; run `upgrade head` on every deploy; remove the `create_all` path. Verify production schema drift first, read-only.
8. **Run Celery worker + beat on Railway** (second service from the same image, Redis add-on). Surface last-run status on System health.
9. **Pick one Telegram implementation** (FastAPI). Delete the Next.js handlers so the rewrite reaches FastAPI.
10. JWT in an httpOnly cookie; refuse default admin password and plaintext token fallback in production.

### P2: Connect the lead-to-cash loop (the core "operating system" work)

11. Add a `campaign_id`/`ad_id`/`utm_*` FK set on **Enquiry**, carried to Quotation → Job → Invoice. Fetch Meta lead details from the Graph API. Route commercial form → CRM Enquiry.
12. **Quote acceptance:** customer accept link + admin accept → `ACCEPTED` → auto-create Job with property and location (approval-gated).
13. **Job completion endpoint** → `COMPLETED` → auto-draft invoice **in FreeAgent** (one invoice source of truth), mirrored locally with `job_id`.
14. **Bank ↔ invoice matching** on FreeAgent sync (amount + reference + date window, with review queue) → sets `matched_invoice_id` → Growth Fund allocates automatically with `campaign_id`.
15. **Per-campaign profitability** (revenue, materials, labour, ad spend) and **Meta CAPI** "Purchase" events on payment.
16. Feed per-campaign profit into the marketing director recommendations.

A domain-event table (`business_events`: enquiry.created, quote.accepted, job.completed, invoice.paid …) processed by the worker is the recommended backbone for 11–16. It gives an audit trail and retries without introducing a message broker beyond the Redis already needed for Celery.

### P3: Consolidate and polish

17. Merge marketing surfaces into `/dashboard/marketing/*`; retire marketing-hub, advertising, content-calendar and the marketing-integrations duplicates; merge CommercialLead into CRM.
18. Merge finance, finance-hub, invoices and expenses into one Money area with tabs.
19. Customer timeline page (enquiries, quotes, jobs, invoices, messages).
20. Restyle all pages on shared `portal-ui` components; responsive tables to cards on mobile.
21. Rebrand the public site to SurfaceCoat (if desired); collapse root docs.
22. Google Ads / GA4 / GSC: implement properly or hide until credentials exist.

### External credentials required (cannot be completed by code alone)

FreeAgent OAuth app; Meta app secret + system user token + ad account + page + pixel/CAPI token + webhook verify token; Telegram bot token + secret; OpenAI/Anthropic key; Redis (Railway add-on) for the worker; optional Google Ads developer token, GA4 and GSC service account; a production test user for automated smoke checks.
