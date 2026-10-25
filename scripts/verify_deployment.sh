#!/usr/bin/env bash
set -Eeuo pipefail

echo "== AEGIS deployment validation =="

command -v docker >/dev/null || { echo "ERROR: Docker is required." >&2; exit 1; }
command -v python >/dev/null || { echo "ERROR: Python is required." >&2; exit 1; }

python scripts/check_dependency_sync.py
python scripts/check_docs_claims.py

ENV_FILE=".env.production"
if [ ! -f "$ENV_FILE" ]; then
    echo "Notice: .env.production not found; using .env.production.example for validation"
    ENV_FILE=".env.production.example"
fi

docker compose \
  --env-file "$ENV_FILE" \
  -f deploy/docker-compose.yml \
  config --quiet

docker build \
  --pull \
  --tag aegis-docintel:security-check \
  --file Dockerfile .

echo "Configuration and image build checks passed."
echo "This does not prove runtime security or application correctness."
