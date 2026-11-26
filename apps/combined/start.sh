#!/bin/sh
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
export PORT="${PORT:-3000}"
LOG=/tmp/rmd-api.log

echo "[rmd] combined start PORT=$PORT image=${RMD_IMAGE_KIND:-unknown}"

if [ -f /api/app/main.py ]; then
  api_bootstrap() {
    cd /api || return 1
    if [ "${DATABASE_MIGRATIONS_MANAGED:-false}" = "true" ] || [ "${ALEMBIC_ON_START:-0}" = "1" ]; then
      echo "[rmd] running alembic upgrade head"
      alembic upgrade head || echo "[rmd] WARN: Alembic failed — see $LOG"
    fi
    exec uvicorn app.main:app --host 127.0.0.1 --port 8000
  }
  (api_bootstrap >>"$LOG" 2>&1) &
  echo "[rmd] FastAPI background pid $! (log $LOG)"
else
  echo "[rmd] WARN: /api missing — web only until Root Directory is cleared (RAILWAY_FIX_NOW.md)"
fi

cd /app || exit 1
if [ ! -f ./server.js ]; then
  echo "[rmd] FATAL: ./server.js missing" >&2
  ls -la /app >&2 || true
  exit 1
fi
exec node server.js