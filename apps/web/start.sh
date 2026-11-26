#!/bin/sh
# Web-only entrypoint (not production login). Combined deploy uses apps/combined/start.sh.
set -e
export HOSTNAME=0.0.0.0
export PORT="${PORT:-3000}"
cd /app
echo "[rmd] web-only start PORT=${PORT} HOSTNAME=${HOSTNAME}"
if [ ! -f ./server.js ]; then
  echo "[rmd] FATAL: ./server.js missing" >&2
  exit 1
fi
exec node server.js