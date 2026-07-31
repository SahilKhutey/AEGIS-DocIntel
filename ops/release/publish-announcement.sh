#!/usr/bin/env bash
# Copy release/v0.3.0/ANNOUNCEMENT.md into the static press site.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
mkdir -p "$ROOT/site/press"

VERSION="${1:-v0.3.0}"
DATE="$(date -u +%Y-%m-%d)"

cp "$ROOT/release/$VERSION/ANNOUNCEMENT.md" "$ROOT/site/press/${DATE}-${VERSION}.md"
cp "$ROOT/release/$VERSION/ANNOUNCEMENT.md" "$ROOT/site/press/${DATE}-${VERSION}.html"
echo "Copied to site/press/${DATE}-${VERSION}.md"
echo "Open a PR with that file to publish."
