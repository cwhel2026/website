#!/bin/sh
set -e
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
cd /api && uvicorn app.main:app --host 127.0.0.1 --port 8000 &
i=0
while [ "$i" -lt 30 ]; do
  if curl -sf "${API_INTERNAL_URL}/health" >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done
cd /app && exec node server.js