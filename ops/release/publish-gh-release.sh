#!/usr/bin/env bash
# Publish the GitHub Release from release/v0.3.0/ANNOUNCEMENT.md
set -euo pipefail

: "${GH_TOKEN:?Set GH_TOKEN to a fine-grained PAT with repo:write}"

VERSION="${1:-v0.3.0}"
NOTES="$(cat release/v0.3.0/ANNOUNCEMENT.md)"

gh release create "$VERSION" \
    --title "AEGIS-DocIntel $VERSION — Deprecation Cleanup" \
    --notes "$NOTES" \
    --target master \
    "release/v0.3.0/MANIFEST.json"

echo "Release $VERSION created."
echo "Next: bash ops/release/publish-announcement.sh"
