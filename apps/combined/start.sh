#!/bin/sh
set -e
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
LOG=/tmp/uvicorn.log
cd /api
uvicorn app.main:app --host 127.0.0.1 --port 8000 >"$LOG" 2>&1 &
UVICORN_PID=$!
i=0
ok=0
while [ "$i" -lt 90 ]; do
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "uvicorn exited before ready (pid $UVICORN_PID)"
    cat "$LOG"
    exit 1
  fi
  if curl -sf "${API_INTERNAL_URL}/health" >/dev/null 2>&1; then
    ok=1
    break
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$ok" -ne 1 ]; then
  echo "FastAPI did not pass /health within 90s — see log:"
  cat "$LOG"
  exit 1
fi
echo "FastAPI ready (pid $UVICORN_PID)"
cd /app && exec node server.js