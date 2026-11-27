# Phase 1 reliability review

Stacked on PR #64. Do not merge or deploy without owner approval.

Fixed: insert inside SQLAlchemy savepoint; lock manual retry and do not resend delivered notifications; reject cancelled/non-Telegram retries; unique atomic photo temporary files and pre-decode pixel cap.

Remaining review blockers: direct delivery and scheduled delivery need shared row-level coordination; per-recipient partial success must remain visible and retriable; external delivery cannot guarantee exactly-once after a crash. Verify that the record marked as test by migration 0022 really is test data before deployment.

Production gates:
- Verify a single dedicated worker with Redis, beat and fresh heartbeats using existing worker deployment instructions.
- Configure persistent private storage for QUOTE_PHOTOS_DIR; copy existing photos before changing paths, verify after restart, back up database and media and test restoration separately.
- Verify /ready against migrated staging database before enabling Railway healthcheck.
- Test labelled Telegram alerts and recover outstanding requests; verify actual receipt.
- Run full CI, including real Postgres concurrency tests, before approving merge.
- Confirm production auto-deploy settings before any merge.

No Railway configuration or production data changed by this review.
