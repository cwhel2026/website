# Integrations

| Integration | Status | Notes |
|-------------|--------|-------|
| PostgreSQL/PostGIS | Local via Docker compose | Not verified in CI with DB |
| Redis | Container only | Unused in Phase 1 |
| OpenAI / Anthropic / Gemini | Not connected | Planned Phase 3+ |
| Weather API | Not connected | Phase 2 |
| Google Maps / routing | Not connected | Phase 2 |
| Address lookup | Not connected | Licensed provider TBD |
| FreeAgent | **Unverified** | OAuth/docs not completed |
| Mettle | **Unverified** | Via FreeAgent feed only |
| Meta / Google Ads | Simulation only (not configured) | Ad spend requires approval; no live API calls |
| Telegram | Webhook stub (503 if unset) | Admin ID allowlist in env |
| OpenAI | Not connected | Optional future layer on tools |
| SMS / WhatsApp | Not connected | Phase 3 |
| Object storage (S3) | Not connected | Phase 2+ for uploads |

No integration is marked “connected” until a successful verified test is recorded here with date and environment.