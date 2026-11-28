# SurfaceCoat production recovery

## Before launch
- Enable PostgreSQL backups in Railway and verify retention and restoration options for the actual plan. Do not assume backups exist.
- Keep quote photos and other uploaded media on persistent storage; back up separately from PostgreSQL.
- Store secrets only in Railway variables; rotate exposed credentials, including Telegram tokens, and never paste them into logs or tickets.
- Keep one Celery beat instance. Verify a fresh scheduler heartbeat, not just process startup.
- Review npm and Python audit artifacts; unresolved high/critical production vulnerabilities block launch.
- Verify owner login, auditor write denial, quote submission, outbox delivery and live weather. Do not send customer messages or spend money during drills.

## Restore drill
CI restores a disposable PostgreSQL dump into a separate database and checks the migration revision and heartbeat records. This does not certify production backups.

For production, provision an isolated database with compatible PostgreSQL version and extensions. Restore the selected backup there, verify schema revision, record counts, sample quotations, invoice/payment links and media availability. Keep workers and outbound integrations disabled on the restored environment. Record the backup timestamp, recovery duration and any missing data. Obtain owner approval before switching production connections. Never restore over the only live database.

## Incident response
Pause outbound integrations and director actions; preserve logs with secrets redacted. Identify the last known good deployment and database revision. Roll back application code only when schema compatibility is confirmed. Restore to an isolated database first. Reconcile payment and notification records before restarting workers to avoid duplicate external actions.

## Outstanding production evidence
Railway backup configuration, persistent media, live restore, provider credentials, actual vulnerability remediation and post-deployment checks require verification. CI success alone is not production certification.
