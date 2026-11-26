# Login / 502 fixes

**Authoritative guide:** [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md)

Quick reminders:

- **502** → Root Directory must be **empty**; Dockerfile `apps/combined/Dockerfile`; start `/app/start.sh`.
- **503 on login** → combined image not running; check `GET /api/ops/status`.
- Owner password = `DEFAULT_ADMIN_PASSWORD` on the website service (synced on API boot; no DB reset).