# Deployment

Target: **Railway** with Docker.

Suggested services:

1. `web` — Next.js (`npm run build` + `next start`).
2. `api` — `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. `postgres` — Railway PostgreSQL with PostGIS extension enabled manually.
4. `redis` — optional until Celery is introduced.

Set `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL` per environment.

Database migrations: move from startup `create_all` to Alembic autogenerate before first production deploy.