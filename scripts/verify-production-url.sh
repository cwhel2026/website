#!/usr/bin/env bash
# Read-only production smoke (no credentials). Exit non-zero if liveness fails.
set -euo pipefail
BASE="${1:-https://website-production-c21e95cd.up.railway.app}"

code_home=$(curl -sS -m 20 -o /tmp/rmd-home.html -w "%{http_code}" "$BASE/" || echo "000")
code_live=$(curl -sS -m 20 -o /tmp/rmd-live.json -w "%{http_code}" "$BASE/api/live" || echo "000")
code_health=$(curl -sS -m 20 -o /tmp/rmd-health.json -w "%{http_code}" "$BASE/health" || echo "000")
code_ready=$(curl -sS -m 20 -o /tmp/rmd-ready.json -w "%{http_code}" "$BASE/api/ready" || echo "000")

echo "BASE=$BASE"
echo "/           HTTP $code_home"
echo "/api/live   HTTP $code_live  $(head -c 120 /tmp/rmd-live.json 2>/dev/null; echo)"
echo "/health     HTTP $code_health $(head -c 120 /tmp/rmd-health.json 2>/dev/null; echo)"
echo "/api/ready  HTTP $code_ready $(head -c 120 /tmp/rmd-ready.json 2>/dev/null; echo)"

login_code=$(curl -sS -m 20 -o /tmp/rmd-login.json -w "%{http_code}" \
  -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"not-a-real@example.com","password":"wrong"}' || echo "000")
echo "POST login (invalid) HTTP $login_code"

if [ "$code_live" = "200" ] || [ "$code_home" = "200" ]; then
  exit 0
fi
exit 1