#!/bin/sh
set -e
export PYTHONPATH="/api:${PYTHONPATH:-}"
cd /api && uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd /app && exec node server.js