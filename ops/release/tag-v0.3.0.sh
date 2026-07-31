#!/usr/bin/env bash
# Idempotent v0.3.0 tagger.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

VERSION="v0.3.0"
SHA="$(git rev-parse HEAD)"

# Pre-flight
python scripts/release_preflight.py

# Generate manifest
python scripts/release_rc_manifest.py \
    --rc 3 \
    --out release/v0.3.0/MANIFEST.json

# Tag (idempotent: re-tagging the same SHA is fine)
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Tag $VERSION already exists at $(git rev-parse "$VERSION")"
else
    git tag -s "$VERSION" "$SHA" -m "AEGIS-DocIntel $VERSION — Deprecation Cleanup"
fi

git push origin "$VERSION"
echo "Pushed $VERSION -> GitHub Actions runs release.yml"
echo "Next: bash ops/release/publish-gh-release.sh"
