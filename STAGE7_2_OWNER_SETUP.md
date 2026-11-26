# Stage 7.2 owner setup (pre-launch)

You do **not** need Facebook, Instagram or ad accounts to start.

## Use today

1. **Launch readiness** dashboard — see what is blocked vs internal-only.
2. **Marketing hub** — budget stays blocked for live spend.
3. **Content studio** — generate drafts; publish simulates until Meta connected.
4. **Telegram** — `#marketing before permission` / `#marketing after permission` on job photos.
5. **Director** — Automations or `POST /marketing/launch/director/run` for daily brief.

## When you register the business

1. Companies House → add `COMPANIES_HOUSE_API_KEY`.
2. Domain email → SMTP vars; enable outreach only after SPF/DKIM/DMARC.

## When you create social accounts

1. Meta Business → `META_ACCESS_TOKEN`, `META_PAGE_ID`, `META_AD_ACCOUNT_ID`.
2. Test **Marketing setup** → Meta insights.
3. Approve content → publish (live only when not simulated).

## Volume

`MARKETING_MEDIA_DIR=/data/marketing_media` on the **API** service (same volume pattern as receipts).

## Launch day

1. Complete checklist in Launch readiness (all non-optional items green or verified).
2. Explicitly approve `live_paid_spend_approved` in budget policy.
3. Run emergency pause test once Meta connected.