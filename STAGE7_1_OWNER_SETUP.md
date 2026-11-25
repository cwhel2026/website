# Stage 7.1 — Owner setup guide (simple steps)

PR #30 merged to `main`. Stage 7.1 adds multi-source research, outreach, content studio, integration centre, and platform API paths.

## 1. Deploy

1. Merge Stage 7.1 PR when CI is green.
2. Run database migrations through `20251125_0012`.
3. On **combined Railway API service**, mount a volume (e.g. `/data`) and set:
   - `MARKETING_MEDIA_DIR=/data/marketing_media`
   - Keep `FINANCE_RECEIPTS_DIR` on the same volume path pattern if receipts already work.

## 2. Research (no outreach yet)

| Step | Action |
|------|--------|
| Companies House | `COMPANIES_HOUSE_API_KEY` |
| Google Places | `GOOGLE_PLACES_API_KEY` (Places API New) |
| OSM | No key — automatic with attribution |

In **Marketing hub** or API `POST /marketing/research/territory`, run territory research. Daily API spend capped by **Budget → research_api_daily_limit_gbp**.

## 3. Email outreach (optional)

| Variable | Purpose |
|----------|---------|
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Transactional SMTP |
| `OUTREACH_FROM_EMAIL`, `OUTREACH_FROM_NAME` | Sender identity |

In Marketing hub budget: enable **outreach_email_enabled** only after SPF/DKIM/DMARC are configured. Draft → approve → send.

## 4. Meta ads

| Variable | Purpose |
|----------|---------|
| `META_ACCESS_TOKEN` | Insights + paused campaign create |
| `META_AD_ACCOUNT_ID` | Ad account |
| `META_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN` | Lead webhooks |

**Approve live paid spend** only when ready. Campaigns create **PAUSED**. Emergency pause hits Meta API when configured.

## 5. Google Ads

| Variable | Purpose |
|----------|---------|
| `GOOGLE_ADS_*` | Customer, developer token, OAuth client |

Live mutate after `GOOGLE_ADS_REFRESH_TOKEN` is stored — dry-run works without it.

## 6. Content & Telegram

- **Content studio** dashboard or API — drafts need approval before publish.
- Telegram: send photo with caption `#marketing before permission` to store marketing media (not receipts).

## 7. Integration centre

**Dashboard → Marketing setup** lists every integration, env vars, and test buttons.

## 8. Still manual / blocked without review

- TikTok auto-publish
- GBP/GA4/GSC live writes (credentials + verification)
- Full Google Ads campaign mutate in production
- Meta lead ads until webhook URL registered in Meta app

See `STAGE7_VERIFICATION_MATRIX.md` for the full checklist.