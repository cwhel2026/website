# Phase 2 security review

Code review, not a penetration test or verified production audit.

- Outbox delivery now refreshes under a row lock; records successful recipients for partial retries. Telegram cannot guarantee exactly-once delivery across a crash before database commit.
- Telegram network and malformed-response errors are normalized without token-bearing URLs. Review HTTP client logging configuration separately.
- Existing owner passwords and disabled state survive startup. DEFAULT_ADMIN_PASSWORD is bootstrap-only for existing accounts; use authorized recovery to rotate. Refuse promotion of a non-owner account.
- Proxy caps request bodies at 16 MiB, times out upstream at 120 seconds, avoids automatic redirects and strips selected transport headers. Validate multi-photo upload UX against this limit.
- Existing JWT startup checks, HttpOnly session and CSRF, webhook validation and read-only auditor tests are present; full permission matrix and secret history scans remain outstanding.
- Dependency CVE scan (pip-audit and npm audit), data retention review, and real Postgres concurrency tests remain outstanding.
- Railway access is required to verify persistent private media, backup restore, worker/Redis heartbeat, readiness and live Telegram receipt. Do not claim these are verified from source.
- CI must pass before merge approval.
