# Integrations

| Integration | Status | Notes |
|-------------|--------|-------|
| PostgreSQL/PostGIS | Local via Docker compose | Not verified in CI with DB |
| Redis | Container only | Unused in Phase 1 |
| OpenAI / Anthropic / Gemini | Not connected | Planned Phase 3+ |
| Weather API | Not connected | Phase 2 |
| Google Maps / routing | Not connected | Phase 2 |
| Address lookup | Not connected | Licensed provider TBD |
| FreeAgent | **Unverified** — CSV fallback active | OAuth env vars; sync endpoint stub |
| Mettle | **Unverified** | Bank feed via FreeAgent when connected |
| Bank CSV import | **Working** (local) | Mettle/FreeAgent export column aliases |
| Meta / Google Ads | Simulation only (not configured) | Ad spend requires approval; no live API calls |
| Telegram | Webhook stub (503 if unset) | Admin ID allowlist in env |
| OpenAI | Not connected | Optional future layer on tools |
| SMS / WhatsApp | Not connected | Phase 3 |
| Object storage (S3) | Not connected | Phase 2+ for uploads |
| Business Director orchestration | **Local only** | Deterministic scan → task queue; no LLM or Celery worker |

No integration is marked “connected” until a successful verified test is recorded here with date and environment.