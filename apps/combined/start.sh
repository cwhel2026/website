#!/bin/sh
# Combined production entrypoint — Next on $PORT (public), FastAPI on 127.0.0.1:8000 (internal).
set -e

export PYTHONPATH="/api:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export HOSTNAME=0.0.0.0
export PORT="${PORT:-3000}"

# Normalise sidecar base URL (Railway may set a trailing slash → //health).
trim_trailing_slashes() {
  printf '%s' "$1" | sed 's:/*$::'
}
API_RAW="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
API_INTERNAL_URL="$(trim_trailing_slashes "$API_RAW")"
export API_INTERNAL_URL

HEALTH_URL="${API_INTERNAL_URL}/health"
READY_URL="${API_INTERNAL_URL}/ready"
STARTUP_TIMEOUT="${RMD_API_STARTUP_TIMEOUT:-120}"

echo "[rmd] combined start PORT=${PORT} HOSTNAME=${HOSTNAME} image=${RMD_IMAGE_KIND:-unknown}"
echo "[rmd] API_INTERNAL_URL=${API_INTERNAL_URL} (raw was: ${API_RAW})"

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
while [ "$i" -lt "$STARTUP_TIMEOUT" ]; do
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "[rmd-api] FATAL: uvicorn exited during startup" >&2
    exit 1
  fi
  if curl -sfS "$HEALTH_URL" >/dev/null 2>&1; then
    api_ok=1
    break
  fi
  i=$((i + 1))
  sleep 1
done

if [ "$api_ok" -ne 1 ]; then
  echo "[rmd-api] FATAL: GET ${HEALTH_URL} did not return HTTP 2xx within ${STARTUP_TIMEOUT}s" >&2
  echo "[rmd-api] Diagnostic: curl -v ${HEALTH_URL}" >&2
  curl -sS -v "$HEALTH_URL" 2>&1 | tail -20 >&2 || true
  kill "$UVICORN_PID" 2>/dev/null || true
  exit 1
fi

if curl -sfS "$READY_URL" >/dev/null 2>&1; then
  echo "[rmd-api] FastAPI GET ${READY_URL} OK (database)"
else
  echo "[rmd-api] WARN: GET ${READY_URL} not OK — check DATABASE_URL (no data reset)"
fi

echo "[rmd-api] FastAPI ready (pid $UVICORN_PID)"
trap 'kill "$UVICORN_PID" 2>/dev/null' INT TERM

cd /app
echo "[rmd-web] starting Next.js on ${HOSTNAME}:${PORT}"
exec node server.js