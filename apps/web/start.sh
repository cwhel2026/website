#!/bin/sh
set -e
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
export PORT="${PORT:-3000}"
cd /app
echo "[rmd] web start image=${RMD_IMAGE_KIND:-unknown} PORT=$PORT HOSTNAME=$HOSTNAME"
if [ ! -f ./server.js ]; then
  echo "[rmd] FATAL: ./server.js missing — Docker build did not produce Next standalone" >&2
  ls -la /app >&2 || true
  exit 1
fi
exec node server.js