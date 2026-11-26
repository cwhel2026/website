#!/usr/bin/env bash
# Regression: trailing slash on API_INTERNAL_URL must not produce //health.
set -euo pipefail

trim_trailing_slashes() {
  printf '%s' "$1" | sed 's:/*$::'
}

for raw in "http://127.0.0.1:8000" "http://127.0.0.1:8000/" "http://127.0.0.1:8000///"; do
  base="$(trim_trailing_slashes "$raw")"
  health="${base}/health"
  if [ "$health" != "http://127.0.0.1:8000/health" ]; then
    echo "FAIL: raw=$raw -> $health"
    exit 1
  fi
done

echo "OK: internal health URL normalisation"