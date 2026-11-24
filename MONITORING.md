# Monitoring and health

## Endpoints

| Path | Use |
|------|-----|
| `GET /health` | Liveness — process up (no database) |
| `GET /ready` | Readiness — PostgreSQL `SELECT 1` |

Railway / Kubernetes should use `/health` for liveness and `/ready` for readiness.

## Headers

Every response includes:

- `X-Request-ID` — echoed from the client or generated; use in logs and support tickets
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, etc.)

## Logs

Run `uvicorn` with platform log shipping. Correlate by `X-Request-ID` once request logging is added (Phase 7 ships middleware only; structured JSON logging is a follow-up).

## Alerts (suggested)

- Ready probe failures > 2 minutes
- 5xx rate spike on `/api/v1/*`
- Login rate-limit (`429`) sustained — possible credential stuffing