#!/usr/bin/env bash
# Smoke-test combined image (requires docker). Does not wipe production data.
set -euo pipefail
IMAGE="${1:-rmd-combined:local}"
PORT="${SMOKE_PORT:-18080}"
JWT_SECRET="${JWT_SECRET:-smoke-test-secret-with-at-least-thirty-two-characters}"
DB_URL="${DATABASE_URL:-postgresql+asyncpg://rmd:rmd_dev_password@host.docker.internal:5432/revive_my_drive}"

echo "Building $IMAGE ..."
docker build -f apps/combined/Dockerfile -t "$IMAGE" .

CID=$(docker run -d --rm \
  -e PORT=3000 \
  -e HOSTNAME=0.0.0.0 \
  -e ENVIRONMENT=development \
  -e JWT_SECRET="$JWT_SECRET" \
  -e DATABASE_URL="$DB_URL" \
  -e RMD_IMAGE_KIND=combined \
  -p "127.0.0.1:${PORT}:3000" \
  "$IMAGE")

cleanup() { docker stop "$CID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

base="http://127.0.0.1:${PORT}"
for i in $(seq 1 90); do
  if curl -sf "$base/api/live" >/dev/null 2>&1; then break; fi
  if [ "$i" -eq 90 ]; then echo "FAIL: /api/live timeout"; exit 1; fi
  sleep 1
done

curl -sf "$base/api/live" | head -c 200
echo ""
curl -sf "$base/health" | head -c 200 || echo "WARN: /health (needs DB if lifespan requires)"
echo ""
echo "Smoke OK (liveness). Full /ready requires reachable Postgres."