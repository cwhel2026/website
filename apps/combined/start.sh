#!/bin/sh
# Combined production entrypoint — Next on $PORT (public), FastAPI on 127.0.0.1:8000 (internal).
set -e

export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
export PYTHONUNBUFFERED=1
export HOSTNAME=0.0.0.0
export PORT="${PORT:-3000}"

echo "[rmd] combined start PORT=${PORT} HOSTNAME=${HOSTNAME} image=${RMD_IMAGE_KIND:-unknown}"

if [ ! -f /app/server.js ]; then
  echo "[rmd] FATAL: /app/server.js missing — combined Docker build failed" >&2
  ls -la /app >&2 || true
  exit 1
fi

if [ ! -f /api/app/main.py ]; then
  echo "[rmd] FATAL: /api/app/main.py missing — Root Directory must be empty; Dockerfile apps/combined/Dockerfile" >&2
  exit 1
fi

cd /api

if [ "${DATABASE_MIGRATIONS_MANAGED:-false}" = "true" ] || [ "${ALEMBIC_ON_START:-0}" = "1" ]; then
  echo "[rmd-api] running alembic upgrade head"
  if ! alembic upgrade head; then
    echo "[rmd-api] FATAL: alembic upgrade head failed" >&2
    exit 1
  fi
  echo "[rmd-api] alembic upgrade head OK"
fi

echo "[rmd-api] starting uvicorn on 127.0.0.1:8000"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info &
UVICORN_PID=$!

(
  while kill -0 "$UVICORN_PID" 2>/dev/null; do
    sleep 2
  done
  echo "[rmd-api] FATAL: uvicorn exited (pid $UVICORN_PID)" >&2
  kill -TERM 0 2>/dev/null || exit 1
) &

i=0
api_ok=0
while [ "$i" -lt 120 ]; do
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "[rmd-api] FATAL: uvicorn exited during startup" >&2
    exit 1
  fi
  if curl -sf "${API_INTERNAL_URL}/health" >/dev/null 2>&1; then
    api_ok=1
    break
  fi
  i=$((i + 1))
  sleep 1
done

if [ "$api_ok" -ne 1 ]; then
  echo "[rmd-api] FATAL: /health did not respond within 120s" >&2
  kill "$UVICORN_PID" 2>/dev/null || true
  exit 1
fi

if curl -sf "${API_INTERNAL_URL}/ready" >/dev/null 2>&1; then
  echo "[rmd-api] FastAPI /ready OK (database)"
else
  echo "[rmd-api] WARN: /ready not OK — check DATABASE_URL and migrations (no data reset required)"
fi

echo "[rmd-api] FastAPI ready (pid $UVICORN_PID)"
trap 'kill "$UVICORN_PID" 2>/dev/null' INT TERM

cd /app
echo "[rmd-web] starting Next.js on ${HOSTNAME}:${PORT}"
exec node server.js