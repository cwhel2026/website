# Railway — Stage 7 marketing variables

Add alongside existing app variables. Secrets via Railway encrypted variables — never commit values.

| Variable | Required | Purpose |
|----------|----------|---------|
| `COMPANIES_HOUSE_API_KEY` | For UK company search | Companies House REST API basic auth key |
| `META_ACCESS_TOKEN` | For Meta insights | Long-lived system user token with ads_read |
| `META_AD_ACCOUNT_ID` | For Meta insights | Numeric ad account (with or without `act_` prefix) |
| `GOOGLE_ADS_CUSTOMER_ID` | Future Google Ads | Customer ID without dashes |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Future Google Ads | Developer token (test or production) |
| `MARKETING_MEDIA_DIR` | Optional | Volume path for uploaded marketing media (default `data/marketing_media`) |
| `MARKETING_SIMULATION_DEFAULT` | Optional | Default `true` — keeps new campaigns in simulation |

Non-secret marketing limits are stored in PostgreSQL (`marketing_budget_policies`) and editable from **Marketing hub → Budget controls**.

Finance and Telegram variables from Stage 6 are unchanged.