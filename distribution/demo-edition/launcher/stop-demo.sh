#!/usr/bin/env bash
# AEGIS-DocIntel Demo Edition — Stop Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_DIR="${PACKAGE_ROOT}/deploy"

echo "Stopping AEGIS Demo containers..."
cd "${DEPLOY_DIR}"
docker compose -f compose.yaml down
echo "[OK] Containers stopped."
