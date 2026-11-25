# Marketing integration setup

## 1. Budget (do first)

1. Open **Dashboard → Marketing hub**.
2. Confirm **Live paid spend** shows **Blocked (default)**.
3. Set daily/platform limits via API `PATCH /api/v1/marketing/budget` or future UI fields.
4. Only enable **Approve live spend** when Meta/Google credentials and approvals are ready.

## 2. Companies House (commercial prospecting)

1. Register at [developer.company-information.service.gov.uk](https://developer.company-information.service.gov.uk/).
2. Create an application API key.
3. Set `COMPANIES_HOUSE_API_KEY` on Railway.
4. In Marketing hub, search e.g. `retail park Preston` — imports deduplicated prospects with source URL and confidence.

## 3. Meta (Facebook / Instagram ads)

1. Meta Business Portfolio with Page, Instagram professional account, Ad Account.
2. Create a Meta app with **Marketing API**; complete permissions for your use case.
3. Generate a long-lived access token with `ads_read` (and later `ads_management` for writes).
4. Set `META_ACCESS_TOKEN` and `META_AD_ACCOUNT_ID`.
5. Use **Integrations** / `GET /api/v1/marketing/meta/insights` to confirm **live read** before any write work.

**Writes** (campaign create, lead forms, publishing) require additional app review — not enabled until verified in matrix.

## 4. Google Ads

1. Google Ads manager account + developer token.
2. OAuth consent and refresh token storage (planned in encrypted credential store).
3. Set `GOOGLE_ADS_CUSTOMER_ID` and `GOOGLE_ADS_DEVELOPER_TOKEN` — connection status only until OAuth complete.

## 5. Google Business Profile / Search Console / GA4

Not connected in Stage 7 Phase A–F partial release. Use Website dashboard for content; GBP API credentials will follow same Integration centre pattern.

## 6. Testing connections

- `GET /api/v1/marketing/platform-status` — integration registry snapshot.
- `GET /api/v1/marketing/meta/insights` — spend when Meta configured.
- No test exposes secret values to the browser or Telegram.