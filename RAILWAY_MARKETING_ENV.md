# Railway — Stage 7 marketing variables

Add alongside existing app variables. Secrets via Railway encrypted variables — never commit values.

| Variable | Required | Purpose |
|----------|----------|---------|
| `COMPANIES_HOUSE_API_KEY` | For UK company search | Companies House REST API basic auth key |
| `META_ACCESS_TOKEN` | For Meta insights | Long-lived system user token with ads_read |
| `META_AD_ACCOUNT_ID` | For Meta insights | Numeric ad account (with or without `act_` prefix) |
| `GOOGLE_ADS_CUSTOMER_ID` | Future Google Ads | Customer ID without dashes |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Future Google Ads | Developer token (test or production) |
| `MARKETING_MEDIA_DIR` | **Recommended** | Mount path on API service volume e.g. `/data/marketing_media` (not shared across separate Railway services) |
| `GOOGLE_PLACES_API_KEY` | Places research | Google Cloud — Places API (New) |
| `META_PAGE_ID` | Organic publish (future) | Facebook Page ID |
| `META_APP_SECRET` | Lead webhooks | App secret for signature verification |
| `META_WEBHOOK_VERIFY_TOKEN` | Lead webhooks | Random string for Meta webhook verify |
| `GOOGLE_ADS_REFRESH_TOKEN` | Google Ads live read/write | OAuth refresh token |
| `GOOGLE_ADS_CLIENT_ID` / `GOOGLE_ADS_CLIENT_SECRET` | Google Ads OAuth | Cloud console OAuth client |
| `GA4_PROPERTY_ID` | Analytics | GA4 property numeric ID |
| `GSC_SITE_URL` | Search Console | e.g. `sc-domain:revivemydrive.co.uk` |
| `GBP_ACCOUNT_ID` | Business Profile | Account ID when API enabled |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Outreach email | Business SMTP (separate from marketing@ if needed) |
| `OUTREACH_FROM_EMAIL` / `OUTREACH_FROM_NAME` | Outreach identity | Visible sender |
| `MARKETING_SIMULATION_DEFAULT` | Optional | Default `true` — keeps new campaigns in simulation |

Non-secret marketing limits are stored in PostgreSQL (`marketing_budget_policies`) and editable from **Marketing hub → Budget controls**.

Finance and Telegram variables from Stage 6 are unchanged.