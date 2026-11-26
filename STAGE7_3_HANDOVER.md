# Stage 7.3 handover — final marketing intelligence (pre-launch)

Marketing development **stops here**. Stage 8 covers Intelligent Business Operations.

## Delivered in 7.3

| Area | What ships | Live vs mock |
|------|------------|--------------|
| Brand intelligence | `MarketingBrandProfile` extended; `GET/PATCH /marketing/launch/brand`; all content AI uses `brand_system_prompt` | Internal |
| Competitor research | Places API only; `POST /marketing/launch/competitors/research`; dashboard in hub | Awaiting `GOOGLE_PLACES_API_KEY` |
| Google SEO clients | Connection verification for GBP / GSC / GA4; SEO + website audit endpoints | Awaiting OAuth & property IDs |
| Commercial pipeline | Full `CommercialPipelineStage` enum; history JSON; `POST .../pipeline` transitions | Internal |
| Job-linked Telegram | `#marketing before/after` + `RMD-…` ref → staging + optional before/after package | Volume + permissions |
| Profitability | `GET /marketing/launch/profitability` — explicit nulls, finance-linked where present | Partial until spend synced |
| Meta leads | Webhook signature + CRM ingest + dedupe (`marketing_meta_leads`) | Awaiting Meta app |
| Launch planner | 30-day draft plan; `official_launch_date` on budget policy | Approval-gated |
| Director | Competitor + profitability evidence; daily Telegram brief via outbox | Telegram vars |
| Hub UI | Brand, competitors, profitability, pipeline stage on prospects | — |

## Owner setup (single checklist)

Use **`RAILWAY_MARKETING_ENV.md`** plus:

1. **Volume:** `MARKETING_MEDIA_DIR=/data/marketing_media` on API.
2. **Research:** `COMPANIES_HOUSE_API_KEY`, optional `GOOGLE_PLACES_API_KEY`.
3. **Pre-launch defaults:** `live_paid_spend_approved=false`, outreach email off until SMTP verified.
4. **At launch:** Meta (`META_*`), Google (`GOOGLE_ADS_*`, `GA4_PROPERTY_ID`, `GSC_SITE_URL`, `GBP_ACCOUNT_ID`), SMTP, Telegram admin IDs.
5. **Official launch date:** set via launch plan API or budget policy; no auto-publish until approvals.

## API map (new / extended)

- `GET|PATCH /api/v1/marketing/launch/brand`
- `GET /api/v1/marketing/launch/competitors` · `POST .../competitors/research`
- `GET /api/v1/marketing/launch/seo` · `GET .../seo/website-audit`
- `GET /api/v1/marketing/launch/profitability`
- `GET|POST /api/v1/marketing/launch/launch-plan`
- `POST /api/v1/marketing/launch/commercial-prospects/{id}/pipeline`
- `POST /api/v1/marketing/webhooks/meta/leads` (verify + ingest)

## Migration

`20251126_0014` — brand columns, pipeline stage, competitor findings, launch plans, meta leads, job media staging, launch date.

## What is intentionally not live

- Automatic ad spend or organic publishing without owner approval.
- Invented competitors, prices, or reviews.
- GBP/GSC/GA4 metrics until OAuth connected (endpoints return `awaiting_credentials`).

## Next: Stage 8

Proceed with **Intelligent Business Operations** on `main` after this PR merges. Do not extend marketing features until product direction changes.