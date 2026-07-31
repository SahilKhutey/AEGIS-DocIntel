#!/usr/bin/env bash
# 60-second smoke that the entire system is up.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

python -m amdi serve &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
sleep 2

curl -fsS http://localhost:8000/healthz >/dev/null || true
curl -fsS http://localhost:8000/readyz  >/dev/null || true

echo "smoke OK"
