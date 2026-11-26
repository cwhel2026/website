# Production authentication investigation (SurfaceCoat / Revive My Drive)

## Root cause

Production login failed **before credential validation**. The Railway **website** service is running a **web-only** Next.js container (`RMD_IMAGE_KIND=web-only`, `embedded_api_image: false`). FastAPI is **not listening** on `127.0.0.1:8000`, so `POST /api/v1/auth/login` returns **503** (`FastAPI sidecar refused connection`). `GET /health` returns Next.js **404 HTML**, not API JSON.

This is **deployment/process architecture**, not wrong `DEFAULT_ADMIN_*` values or a missing admin row (those cannot be checked until the API starts).

## Intended architecture

**One combined Railway service**: repo-root `Dockerfile`, start command `/app/start.sh` (Next + Uvicorn). Environment variables remain on the website service. Root directory may stay `apps/web` if **Build → Dockerfile path** is the **repository root** `Dockerfile` and **Deploy → start** is `/app/start.sh`.

## Verification checklist (production)

After redeploy:

| Check | Expected |
|--------|----------|
| `GET /health` | JSON `{"status":"ok",...}` |
| `GET /api/deploy-hint` | `api_sidecar_reachable: true`, `combined_deploy: true` |
| `GET /api/ops/status` | `api.reachable: true` |
| `POST /api/v1/auth/login` | 401 for bad password (not 503) |

**Status at last agent check (before this PR merge):** all failed except ops JSON — API still unreachable; **production login not verified**.

## Code changes in this fix

- **Owner provisioning** (`apps/api/app/services/owner_provisioning.py`): create/update owner from `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD`; optional legacy email migration; `rotate_owner_password` for recovery.
- **Bootstrap** uses `ensure_owner_from_env` on startup (existing DB retained; hash synced when env password changes).
- **`ADMIN_SETUP_KEY`**: `POST /api/v1/auth/owner/recover` for owner password reset (rate-limited 5/min).
- **Production startup**: weak default admin password **logs critical** instead of crashing uvicorn (API can start so you can log in after combined deploy).
- **Login UI**: SurfaceCoat branding (charcoal/gold/white), show/hide password, loading, user-facing errors only; recovery page without env var names.
- **API client**: `ApiError` + `mapLoginError` for 401/503/429.
- **Deploy hint**: `combined_deploy` only when `RMD_IMAGE_KIND=combined` **and** `/health` on the internal API succeeds.

## `DEFAULT_ADMIN_PASSWORD` behaviour

On **each API boot**, the owner account for `DEFAULT_ADMIN_EMAIL` gets its password hash **updated** if it does not match the env value. Changing Railway `DEFAULT_ADMIN_PASSWORD` therefore **updates the live owner password** for that email (no DB reset).

## Railway configuration (required)

1. **Build**: Dockerfile = repository root `Dockerfile` (not `apps/web/Dockerfile`).
2. **Deploy**: Start command `/app/start.sh`; health check path `/health`.
3. Ensure `DATABASE_URL`, `SYNC_DATABASE_URL`, `JWT_SECRET` (≥32 chars), `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD` are set on this service.
4. Optional: `ADMIN_SETUP_KEY` (long random) for owner recovery URL `/dashboard/login/recover`.
5. Redeploy and confirm `/health` JSON before testing login.

## Tests

- `apps/api/tests/test_auth_login.py` — hash, token expiry, provisioning mocks, integration (with `RUN_INTEGRATION_TESTS=1`).
- `apps/web/src/lib/api-errors.test.mjs` — `node --test` error mapping.

## Remaining blockers

1. **Redeploy** combined image on Railway (user action).
2. **Confirm** production `/health` and login with owner credentials (agent cannot use owner password from chat).