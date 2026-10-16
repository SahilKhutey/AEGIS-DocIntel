#!/usr/bin/env bash
# scripts/cold_start_check.sh — "README as a test".
#
# Simulates a brand-new user: creates a FRESH virtualenv and runs the exact commands
# the README's "Developer & Test Suite (Cold-Start Safe)" section tells them to run.
# CI runs this on every push (job: cold-start), so the documented install path can
# never silently break again.
#
# Why: the README once told strangers to `pip install -r requirements.txt && pytest`
# while CI installed something different. `hypothesis` and the Office-format libraries
# were undeclared, so the documented path aborted with "Interrupted: 2 errors during
# collection" and ZERO tests run — while CI-on-a-maintainer-machine looked fine.
#
# The commands below MUST match the README code block verbatim;
# scripts/check_docs_claims.py (and tests/test_docs_claims.py) enforce that.
#
# Usage:   scripts/cold_start_check.sh            # uses python3, temp venv
#          PYTHON=python3.13 scripts/cold_start_check.sh
#          KEEP_VENV=1 scripts/cold_start_check.sh   # keep the venv for inspection
set -euo pipefail

PYTHON="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$(mktemp -d)/venv"

cleanup() { [[ "${KEEP_VENV:-0}" == "1" ]] || rm -rf "$(dirname "$VENV_DIR")"; }
trap cleanup EXIT

# README-COMMANDS-BEGIN
README_COMMANDS=(
  "pip install -r requirements-core.txt -r requirements-dev.txt"
  "pytest tests/"
)
# README-COMMANDS-END

echo "== cold-start: fresh venv at $VENV_DIR ($("$PYTHON" --version))"
"$PYTHON" -m venv "$VENV_DIR"
export PATH="$VENV_DIR/bin:$PATH"
python -m pip install --quiet --upgrade pip

cd "$REPO_ROOT"
for cmd in "${README_COMMANDS[@]}"; do
  echo
  echo "\$ $cmd"
  eval "$cmd"
done

echo
echo "== cold-start: PASSED — the README's documented path works from a clean machine"
