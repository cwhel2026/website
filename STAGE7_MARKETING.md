# Stage 7 — AI Marketing & Customer Acquisition

Revive My Drive Ltd marketing department builds on Phase 4 capacity intelligence and Stage 6 finance data. **Live paid advertising and external outreach remain blocked by default** until owner approval and credentials are verified.

## Architecture

- **API** (`apps/api/app/routers/marketing.py`): budget policy, marketing director plans, territory intelligence, Companies House prospect import, Meta insights read, profitability snapshot, commercial outreach drafts.
- **Models** (`apps/api/app/models/marketing_ops.py`): budget policy, deduplicated commercial prospects, outreach messages, content items, media assets, territory scores.
- **Workers**: `rmd.marketing_capacity_snapshot` (existing); scheduled marketing reports planned in Celery beat (manual trigger via Automations until beat enabled).
- **Dashboard**: `/dashboard/marketing-hub` mobile-first command centre.
- **Telegram / AI assistant**: tools `marketing_capacity`, `marketing_weekly_spend`, `marketing_director_plan`, `marketing_profitability`.

## Phases (delivery status)

| Phase | Scope | Status |
|-------|--------|--------|
| A | Models, migration 0011, budget enforcement, integration status | **In PR** |
| B | Commercial prospect engine (Companies House), outreach drafts (GDPR) | **Partial** |
| C | Meta insights read; Google connection status; campaign simulation | **Partial** |
| D | Content studio tables; publishing pipelines | **Schema only** |
| E | Territory intelligence, profitability funnel, capacity linkage | **Partial** |
| F | Director daily plan, Telegram tools, hub UI, docs | **Partial** |

## Owner approvals

1. **Budget policy** — `live_paid_spend_approved` must be true for non-simulation campaigns.
2. **Approvals queue** — AD_SPEND approvals before launch.
3. **Outreach** — messages stay `pending_approval`; no SMTP send in this release without further integration.

## Honest limitations

- Google Ads live read/write requires OAuth refresh token storage (not yet in vault).
- Meta campaign create/publish requires Marketing API app review and verified tokens.
- Attribution ROAS is **provisional** until enquiry/job links are attached to attribution events.
- TikTok / GBP organic publish uses approval queues; automatic publish where API not configured is not claimed.

See `STAGE7_VERIFICATION_MATRIX.md`, `RAILWAY_MARKETING_ENV.md`, `MARKETING_INTEGRATION_SETUP.md`, and `MARKETING_COMPLIANCE.md`.