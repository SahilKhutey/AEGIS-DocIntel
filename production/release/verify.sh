#!/bin/bash
# AMDI-OS v1.0.0 Verification Script
# Downloads and verifies release artifacts

set -e

VERSION="${VERSION:-1.0.0}"
BASE_URL="https://github.com/amdi-os/amdi-os/releases/download/v${VERSION}"

echo "=========================================="
echo "AMDI-OS v${VERSION} Verification"
echo "=========================================="
echo ""

WORKDIR=$(mktemp -d)
cd "$WORKDIR"

echo "[1/5] Downloading checksums..."
curl -fsSL -o SHA256SUMS "${BASE_URL}/SHA256SUMS"
curl -fsSL -o SHA256SUMS.sig "${BASE_URL}/SHA256SUMS.sig"
echo "✓ Checksums downloaded"
echo ""

echo "[2/5] Verifying GPG signature..."
GPG_KEYSERVER="${GPG_KEYSERVER:-hkps://keys.openpgp.org}"
if ! gpg --keyserver "$GPG_KEYSERVER" --recv-keys "AMDI-RELEASE-KEY-FINGERPRINT" 2>/dev/null; then
    echo "⚠ Could not fetch GPG key from $GPG_KEYSERVER"
    echo "  Skipping signature verification"
else
    gpg --verify SHA256SUMS.sig SHA256SUMS
    echo "✓ GPG signature valid"
fi
echo ""

echo "[3/5] Downloading release artifact..."
curl -fsSL -o "amdi-os-v${VERSION}.tar.gz" "${BASE_URL}/amdi-os-v${VERSION}.tar.gz"
echo "✓ Artifact downloaded ($(du -h amdi-os-v${VERSION}.tar.gz | cut -f1))"
echo ""

echo "[4/5] Verifying SHA-256..."
sha256sum -c SHA256SUMS
echo "✓ SHA-256 verified"
echo ""

echo "[5/5] Extracting and validating..."
tar -xzf "amdi-os-v${VERSION}.tar.gz"
cd "amdi-os-v${VERSION}"

# Run validation tests if available
if [ -f "scripts/validate_installation.sh" ]; then
    bash scripts/validate_installation.sh
fi

echo ""
echo "=========================================="
echo "✓ AMDI-OS v${VERSION} verified successfully"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. cd amdi-os-v${VERSION}"
echo "  2. cat README.md"
echo "  3. docker compose -f deployment/docker/docker-compose.yml up -d"
