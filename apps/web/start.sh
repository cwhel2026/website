#!/bin/sh
# Web-only image entrypoint (Root Directory = apps/web).
set -e
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
cd /app
exec node server.js