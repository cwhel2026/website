#!/bin/sh
# Bind $PORT (Next) immediately; boot API/Alembic in the background.
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
LOG=/tmp/rmd-api.log

api_bootstrap() {
  cd /api || return 1
  if [ "${DATABASE_MIGRATIONS_MANAGED:-false}" = "true" ] || [ "${ALEMBIC_ON_START:-0}" = "1" ]; then
    echo "Running alembic upgrade head..."
    if ! alembic upgrade head; then
      echo "WARN: Alembic failed — API may not start; see $LOG"
    fi
  fi
  exec uvicorn app.main:app --host 127.0.0.1 --port 8000
}

(api_bootstrap >>"$LOG" 2>&1) &
echo "FastAPI bootstrap pid $! (log: $LOG)"
cd /app || exit 1
exec node server.js