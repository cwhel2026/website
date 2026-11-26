# Stage 7 verification matrix

| Capability | Implemented | Local tests | Sandbox | Live read | Live write | Blocker |
|------------|-------------|-------------|---------|-----------|------------|---------|
| Budget policy enforcement | Yes | Yes | N/A | N/A | N/A | — |
| Emergency pause | Yes | Yes | N/A | N/A | N/A | — |
| Marketing director daily/weekly plan | Yes | Partial | N/A | N/A | N/A | — |
| Territory intelligence scores | Yes | No | N/A | N/A | N/A | — |
| Companies House prospect import | Yes | No | With API key | With API key | N/A | `COMPANIES_HOUSE_API_KEY` |
| Commercial outreach drafts | Yes | No | N/A | N/A | No send | SMTP/provider TBD |
| Meta account insights (7d spend) | Yes | No | With token | With token | No | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` |
| Meta campaign launch | Simulated | Yes | No | No | No | App review + write scopes |
| Google Ads reporting | Status only | No | No | No | No | OAuth + client library |
| Profitability snapshot | Yes | No | N/A | N/A | N/A | Attribution linking incomplete |
| Marketing hub UI | Yes | Manual | N/A | N/A | N/A | — |
| Telegram marketing tools | Yes | Partial | N/A | N/A | N/A | — |
| Content calendar publish | Schema | No | No | No | No | Meta/GBP write APIs |
| Celery marketing daily report | Yes | No | N/A | N/A | N/A | Beat schedule enabled |
| Multi-source prospect research | Yes | Partial | With API keys | With API keys | N/A | CH + Places + OSM |
| Google Places research | Yes | Partial | With key | With key | N/A | GOOGLE_PLACES_API_KEY |
| OSM Overpass research | Yes | Yes | N/A | N/A | N/A | Attribution required |
| SMTP outreach send | Yes | Partial | With SMTP | With SMTP | Requires approval | outreach_email_enabled |
| Meta paused campaign create | Yes | No | With token | With token | App review | PAUSED default |
| Meta emergency pause | Yes | No | With token | With token | — | |
| Google Ads search (transport) | Yes | Partial | With refresh | With refresh | OAuth | Dry-run default |
| Content studio AI drafts | Yes | No | With OpenAI | With OpenAI | — | Approval queue |
| Telegram #marketing photos | Yes | No | N/A | N/A | — | Volume for media |
| Integration setup centre UI | Yes | Manual | N/A | N/A | N/A | |
| GBP / GA4 / GSC | Scaffold | No | No | No | No | Credentials TBD |
| Pre-launch readiness centre | Yes | Yes | N/A | N/A | N/A | |
| Proactive director history | Yes | Partial | N/A | N/A | N/A | |
| Before/after compositor | Yes | Yes | N/A | N/A | N/A | Pillow formats |
| Organic publish idempotency | Yes | No | Simulated | With Meta | App review | |
| Funnel attribution journey | Yes | Partial | N/A | N/A | N/A | Collected revenue |