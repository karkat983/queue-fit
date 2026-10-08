#!/usr/bin/env bash
# Wait until the target service answers, then confirm the worker count.
#   scripts/healthcheck.sh [base_url] [timeout_seconds]
set -euo pipefail
BASE_URL=${1:-http://localhost:8080}
TIMEOUT=${2:-60}

deadline=$(( $(date +%s) + TIMEOUT ))
until curl -sf -o /dev/null "$BASE_URL/get"; do
  if (( $(date +%s) > deadline )); then
    echo "service at $BASE_URL not healthy after ${TIMEOUT}s" >&2
    exit 1
  fi
  sleep 1
done

latency=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/get")
workers=$(docker compose logs httpbin 2>/dev/null | grep -c "Booting worker" || true)
echo "healthy: $BASE_URL/get in ${latency}s; gunicorn workers booted: ${workers}"
