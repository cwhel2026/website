#!/bin/sh
set -e
export PYTHONPATH="/api:${PYTHONPATH:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:8000}"
cd /api && uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 2
cd /app && exec node server.js