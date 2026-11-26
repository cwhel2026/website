# SurfaceCoat Ltd — Meta marketing director upgrade

## Audit summary (before this change)

| Area | Status |
|------|--------|
| Meta insights read, paused campaign create, lead webhook → CRM | Reused |
| Budget controls + emergency pause | Reused (defaults → £150/week) |
| Google Ads | Retained, **not** primary |
| AI content studio / organic auto-publish | **De-prioritised** in UI (legacy pages kept) |
| Pixel, CAPI, organic import, 9-tab dashboard | **New in this PR** |
| Live campaign launch via `ad_adapters` | Still blocked without approval + credentials |
| Profit attribution end-to-end | Partial (existing attribution journey) |

## Implemented in this PR

- Migration `20251126_0015` — organic posts, snapshots, director mode, launch programme fields
- Organic post sync (Graph API + webhook `/meta/feed` + Celery every 3h)
- Rule-based post analysis (angles, misleading claim flags)
- Organic → paid boost recommendations (approval required)
- Weekly creative brief with **Copy for ChatGPT**
- Meta connection wizard + live connection test
- CAPI sender module (`consent_attested` required)
- SurfaceCoat mobile marketing dashboard (`/dashboard/marketing/*`)
- Default budget £150/week, Preston 20-mile geo, 4-week £600 programme
- Brand seed: SurfaceCoat colours

## Meta permissions (typical)

`pages_read_engagement`, `pages_read_user_content`, `instagram_basic`, `instagram_manage_insights`, `ads_read`, `ads_management`, `leads_retrieval`, `business_management` — **ads_management** and **leads_retrieval** often need App Review.

## Railway environment variables

| Variable | Purpose |
|----------|---------|
| `META_ACCESS_TOKEN` | Graph + Marketing API |
| `META_PAGE_ID` | Page posts |
| `META_INSTAGRAM_ACTOR_ID` | IG media |
| `META_AD_ACCOUNT_ID` | `act_…` insights & campaigns |
| `META_APP_SECRET` | Webhook signature |
| `META_WEBHOOK_VERIFY_TOKEN` | Webhook verify |
| `META_PIXEL_ID` | Pixel / CAPI |
| `META_CAPI_DATASET_TOKEN` | Optional CAPI token |
| `PUBLIC_API_BASE_URL` | Webhook URLs |

Webhooks:

- `GET/POST /api/v1/marketing/webhooks/meta/leads`
- `GET/POST /api/v1/marketing/webhooks/meta/feed`

## Connection steps (owner)

1. Meta Business Portfolio + verified business (recommended)
2. Developer app → Marketing API + Webhooks
3. Long-lived token or system user token → Railway
4. Subscribe webhooks to your public URL
5. Marketing → Integrations → **Test connection**
6. Publish posts manually on FB/IG → **Sync from Meta**
7. Keep **live spend approval OFF** until March 2027 launch readiness

## Pre-launch rules

- `live_paid_spend_approved` defaults **false**
- `MARKETING_SIMULATION_DEFAULT` remains **true**
- No fictional dashboard numbers — empty/disconnected states shown

## Not claimed as production-ready until

- Live Meta credentials tested (page posts + insights return data)
- Alembic `0015` applied on production Postgres
- Owner verifies budget pause and lead webhook with real form submission

## Tests

`tests/test_organic_post_analysis.py`, existing `test_budget_controls.py`

## Remaining (future PRs)

- Full funnel profit metrics on dashboard widgets
- Telegram inline approve/pause buttons
- Boost via `object_story_id` with objective compatibility checks
- GA4 / Google Ads deprioritised UI only (APIs unchanged)