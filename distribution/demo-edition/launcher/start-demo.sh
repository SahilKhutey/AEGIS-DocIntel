#!/usr/bin/env bash
# AEGIS-DocIntel Demo Edition — Unix/macOS Launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_DIR="${PACKAGE_ROOT}/deploy"

echo "===================================================================="
echo "           AEGIS-DocIntel — Protected Demo Edition v1.1.0           "
echo "   Structured Document Intelligence & Context Optimization Workbench "
echo "===================================================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is required but not installed."
    exit 1
fi

echo "[1/3] Starting AEGIS Demo containers..."
cd "${DEPLOY_DIR}"
docker compose -f compose.yaml up -d

echo "[2/3] Waiting for workbench readiness..."
TARGET_URL="http://localhost:3000"
for i in {1..30}; do
    if curl -s -f "${TARGET_URL}/health" > /dev/null 2>&1; then
        echo "[OK] Workbench ready at ${TARGET_URL}"
        break
    fi
    sleep 1
    printf "."
done

echo ""
echo "[3/3] Ready! Open ${TARGET_URL} in your browser to start."
