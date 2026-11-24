# Deployment

Target: **Railway** (or any Docker host) with separate **web** and **api** services.

## Checklist before first production deploy

1. Set `ENVIRONMENT=production`, `JWT_SECRET` (≥32 random chars), and change `DEFAULT_ADMIN_PASSWORD`.
2. Point `DATABASE_URL` at managed PostgreSQL (enable PostGIS when you need geometry).
3. Set `CORS_ORIGINS` to your public dashboard origin(s).
4. Set `NEXT_PUBLIC_API_URL` to the public API URL used by the browser.
5. Run integration smoke: `RUN_INTEGRATION_TESTS=1 pytest tests/test_smoke_integration.py -q` in `apps/api`.
6. Plan Alembic migrations instead of relying on `create_all` long term.

## Docker Compose (production-shaped local)

```bash
cp .env.example .env
# edit JWT_SECRET, DEFAULT_ADMIN_PASSWORD, POSTGRES_PASSWORD

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

- API: `http://localhost:8000/health`
- Web: `http://localhost:3000`

## Railway service layout

| Service | Build | Start |
|---------|-------|--------|
| `api` | `apps/api/Dockerfile` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `web` | `apps/web/Dockerfile` | `node server.js` (standalone Next output) |
| `postgres` | Plugin | Enable PostGIS manually if required |
| `redis` | Plugin | Optional until Celery |

### Required variables

**API:** `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `ENVIRONMENT=production`, `DEFAULT_ADMIN_PASSWORD`

**Web build arg / env:** `NEXT_PUBLIC_API_URL`

## Rate limits (public abuse protection)

- `POST /api/v1/quotations/instant` — 12/minute per IP
- `POST /api/v1/auth/login` and `/token` — 30/minute per IP
- `GET /api/v1/marketing/flyer/{slug}` — 60/minute per IP

For multi-instance deploys, replace in-memory limits with Redis-backed limits (not in Phase 7).