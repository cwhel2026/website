# Railway deployment verification (Revive My Drive)

Repository: `cwhel2026/website` · branch: `main`

## Service layout

| Service | Root directory | Builder | Health |
|---------|----------------|---------|--------|
| Web | `apps/web` | `apps/web/Dockerfile` | `GET /` and `GET /api/version` |
| API | `apps/api` | `apps/api/Dockerfile` | `GET /health` and `GET /ready` |

## Checklist after each production deploy

1. **Repository / branch** — Railway GitHub source points at `cwhel2026/website` and tracks `main`.
2. **Commit SHA** — Compare Railway deploy commit with `curl -s https://<web-host>/api/version` → `git_commit`, and `curl -s https://<api-host>/health` → `git_commit`.
3. **Root directories** — Web service: `apps/web`. API service: `apps/api`. Wrong root causes Railpack/README-only builds.
4. **Web build args** — `NEXT_PUBLIC_API_URL` must be the public API base URL (no trailing slash). Set `NEXT_PUBLIC_GIT_COMMIT` via Docker build args in Railway if not injected automatically.
5. **API env** — `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (include production web origin), `ENVIRONMENT=production`, `GIT_COMMIT` (optional).
6. **CORS** — Browser quote wizard calls API from web origin; API `CORS_ORIGINS` must list the live web URL.
7. **Postgres** — `GET /ready` returns `database: ok`.
8. **Public API** — `GET /api/v1/public/coverage?postcode=L39` from outside Railway.
9. **Quotation flows** — `POST /api/v1/quotations/provisional` returns price without CRM side effects; `POST /api/v1/quotations/submit` requires customer details.

## Build version identifiers

- **Web**: `apps/web/src/app/api/version/route.ts` (reads `NEXT_PUBLIC_GIT_COMMIT`).
- **API**: `apps/api/app/routers/health.py` (reads `GIT_COMMIT` settings).

Do not expose secrets in these endpoints.

## Common failure: old public site

Symptoms: gradient placeholders, old copy, missing `/commercial`. Usually **web service root still at repo root** or deploy from stale branch. Fix root directory, redeploy from latest `main`, hard-refresh browser.