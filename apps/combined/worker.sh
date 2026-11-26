#!/bin/sh
# Railway "worker" service entrypoint (same image as the website service).
# Runs ONE Celery worker with the beat scheduler embedded. Keep this service at
# exactly 1 replica: a second replica would start a second beat (duplicate slots
# are skipped by the task guard, but one scheduler is the intended design).
set -e

export PYTHONPATH="/api:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
cd /api

if [ -z "${REDIS_URL:-}${CELERY_BROKER_URL:-}" ]; then
  echo "[rmd-worker] FATAL: REDIS_URL (or CELERY_BROKER_URL) is not set" >&2
  exit 1
fi

# The website service owns migrations; wait for it rather than racing it.
WAIT="${RMD_WORKER_SCHEMA_WAIT:-300}"
i=0
until python -m app.schema.cli status >/dev/null 2>&1; do
  i=$((i + 5))
  if [ "$i" -ge "$WAIT" ]; then
    echo "[rmd-worker] FATAL: database schema not at Alembic head after ${WAIT}s" >&2
    python -m app.schema.cli status >&2 || true
    exit 1
  fi
  echo "[rmd-worker] waiting for schema migration (${i}s)"
  sleep 5
done

echo "[rmd-worker] schema at head; starting celery worker + beat"
exec celery -A app.worker.celery_app worker --beat \
  --concurrency="${CELERY_CONCURRENCY:-2}" \
  --loglevel=info \
  --schedule=/tmp/celerybeat-schedule
