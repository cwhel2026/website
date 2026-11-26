# Stage 7.2 — Pre-launch marketing readiness

Business is **pre-launch**: no Meta/Google accounts required to use internal marketing.

## New capabilities

- **Proactive AI director** — `MarketingDirectorRun` history, daily cycle with cluster/seasonal/underserved recommendations (`POST /marketing/launch/director/run`)
- **Pre-launch control centre** — `GET /marketing/launch/readiness`
- **Commercial verticals** — 14+ search templates across North West areas
- **Before/after compositor** — Pillow renders Facebook/IG/story formats (crop + label only)
- **Content calendar** — `GET /marketing/content/calendar`
- **Organic publish path** — simulated until `META_PAGE_ID` + token; idempotent `marketing_publication_log`
- **Funnel attribution** — `GET /marketing/launch/attribution-journey` (collected revenue only)
- **Experiments** — evaluate with minimum sample size
- **Telegram** — marketing patterns in deterministic assistant tools

## Owner without external accounts

Works now: prospect research (CH/OSM), content drafts, before/after renders, calendar, director briefs, experiments (draft), budget blocks.

Requires accounts later: live Meta/IG publish, live ads, GBP/GA4/GSC, SMTP outreach.

## Migration

`20251126_0013` — brand profile, director runs, publication log, rendered creatives, prospect prioritisation fields.

See `STAGE7_2_OWNER_SETUP.md` and updated verification matrix.