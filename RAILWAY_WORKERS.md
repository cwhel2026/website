# Railway — background workers (Phase 1)

Supersedes the worker section of `RAILWAY_STAGE3.md`.

## Architecture

```
Postgres ──┬── website  (apps/combined image, /app/start.sh)  → site + API, runs migrations
           └── worker   (same image,         /app/worker.sh) → Celery worker + embedded beat
Redis ─────┴── broker + task locks (website only enqueues; worker consumes)
```

- **One** worker service, **exactly 1 replica**. Beat is embedded (`--beat`), so a second replica
  would run a second scheduler. Duplicate slots are skipped by the task guard, but one scheduler is
  the intended design.
- The website service owns migrations. `worker.sh` waits up to 300 s for the schema to reach
  Alembic head, then starts. It exits non-zero (and Railway restarts it) if Redis is not configured or
  the schema never arrives.
- Every scheduled task is guarded (`app/worker/guard.py`):
  - **Slot dedupe:** one run per task per scheduled minute (`rmd:slot:*`, Redis `SET NX`).
  - **Overlap lock:** a long run blocks the next tick instead of running twice (`rmd:lock:*`).
  - **Retries:** network/DB errors retry twice with exponential backoff (30 s, cap 10 min, jitter).
    Other errors fail immediately and are recorded.
- Evidence is written to Postgres, not just logs:
  - `scheduler_heartbeats` — beat writes every minute; the worker writes on start.
  - `background_job_runs` — every task run with status, timing and error.

## Step-by-step

1. **Redis.** Project → **+ New** → **Database** → **Redis**. Nothing else to configure.
2. **Worker service.** Project → **+ New** → **GitHub Repo** → this repository.
   - Settings → **Source** → Root directory: *(empty)*.
   - Settings → **Config-as-code** → Railway config file: `apps/combined/railway.worker.toml`.
     This sets the Dockerfile, start command `/app/worker.sh` and 1 replica. Without it Railway uses
     the root `railway.toml` and starts a second website.
   - Settings → **Networking**: no public domain needed.
3. **Variables.** Use project **Shared Variables** so website and worker cannot drift. Both services need:

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (the app adds `+asyncpg` itself) |
   | `SYNC_DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
   | `REDIS_URL` | `${{Redis.REDIS_URL}}` |
   | `JWT_SECRET` | same value on both |
   | `ENVIRONMENT` | `production` |
   | `FINANCE_TOKEN_ENCRYPTION_KEY` | 32+ random characters, same on both (worker decrypts FreeAgent tokens) |
   | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_*` | as already set on website (notifications are sent by the worker) |
   | `META_*`, `FREEAGENT_*`, `SMTP_*`, `OPENAI_API_KEY` | as already set on website |

   Website only: `META_APP_SECRET` (webhook signature, required, or Meta webhooks are refused with 503),
   `EMAIL_INBOUND_WEBHOOK_SECRET` (inbound-email webhook, required, or it is refused),
   `E2E_AUDITOR_EMAIL` / `E2E_AUDITOR_PASSWORD` (see `docs/E2E_TESTING.md`).

   Generate secrets locally, never in chat: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
4. **Deploy** the website first (applies migrations), then the worker.
5. **Verify** in the portal → **System health** (or `GET /api/v1/ops/workers`):
   - Within 2 minutes: *Scheduler heartbeat* shows a time under 2 minutes old and overall is not
     `no_worker_evidence` / `scheduler_stale`.
   - `scheduler-heartbeat` row: status **OK**.
   - Each other task stays **Never run** until its schedule fires (for example, notification delivery
     every 2 minutes, appointment weather risk hourly at :15, HQ weather every 3 hours). A task is only verified once it shows a
     **Last success**.
   - Worker logs (Railway → worker → Deployments → View logs) show
     `[rmd-worker] schema at head; starting celery worker + beat` and `beat: Starting...`.

## Status meanings (System health)

| Overall | Meaning | Action |
|---------|---------|--------|
| `ok` | Beat heartbeat fresh, no recent failures | — |
| `degraded` | Heartbeat fresh, at least one task's latest run failed | Read *Recent failures* |
| `scheduler_stale` | Heartbeat older than 3 minutes | Worker crashed or paused; check worker logs |
| `no_worker_evidence` | No heartbeat ever recorded | Worker service not deployed or never started |
| `broker_unreachable` | API cannot reach Redis | Check `REDIS_URL` on website |

## Cost and safety

The worker never launches paid advertising: ad launches require an approved `AD_SPEND` request in
**Approvals** and remain simulated unless live Meta credentials and the live-spend policy are set.
Customer emails are not sent unless SMTP is fully configured; otherwise they are recorded as
`not_sent_smtp_unconfigured`, never as sent.
