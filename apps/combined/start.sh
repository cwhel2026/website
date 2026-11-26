#!/bin/sh
set -e
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
LOG=/tmp/uvicorn.log
cd /api
if [ "${DATABASE_MIGRATIONS_MANAGED:-false}" = "true" ] || [ "${ALEMBIC_ON_START:-0}" = "1" ]; then
  echo "Running alembic upgrade head..."
  if ! alembic upgrade head; then
    echo "Alembic failed — check SYNC_DATABASE_URL / DATABASE_URL and Postgres reachability."
    exit 1
  fi
fi
uvicorn app.main:app --host 127.0.0.1 --port 8000 >>"$LOG" 2>&1 &
echo "FastAPI starting in background (log: $LOG)"
cd /app && exec node server.js