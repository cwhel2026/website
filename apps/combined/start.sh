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

if [ -f /api/app/main.py ]; then
  (api_bootstrap >>"$LOG" 2>&1) &
  echo "FastAPI bootstrap pid $! (log: $LOG)"
else
  echo "ERROR: /api missing — image is not combined. Railway → clear Root Directory → /railway.toml → apps/combined/Dockerfile" >&2
fi
if [ ! -f /app/server.js ]; then
  echo "ERROR: /app/server.js missing — Docker build failed or wrong image." >&2
  exit 1
fi
cd /app || exit 1
exec node server.js