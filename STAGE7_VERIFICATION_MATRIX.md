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
| Celery marketing daily report | Planned | No | N/A | N/A | N/A | Beat schedule |