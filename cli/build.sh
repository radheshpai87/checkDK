#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Build the checkdk CLI into a standalone single-file binary using PyInstaller.
#
# Usage:
#   cd cli
#   ./build.sh
#
# Output: cli/dist/checkdk  (or cli/dist/checkdk.exe on Windows)
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "──────────────────────────────────────────────"
echo "  checkdk CLI — PyInstaller Build"
echo "──────────────────────────────────────────────"
echo ""

# ── Ensure build dependencies ────────────────────────────────────────────────
echo "→ Checking dependencies..."
pip install -e . --quiet 2>/dev/null
pip install pyinstaller --quiet 2>/dev/null
echo "  ✓ Dependencies ready"

# ── Clean previous build artifacts ───────────────────────────────────────────
echo "→ Cleaning previous builds..."
rm -rf build/checkdk dist/
echo "  ✓ Cleaned"

# ── Build using the existing spec file ───────────────────────────────────────
echo "→ Building binary with PyInstaller..."
echo ""
pyinstaller checkdk.spec --noconfirm --clean

echo ""
echo "──────────────────────────────────────────────"

# ── Verify the binary ────────────────────────────────────────────────────────
BINARY="$SCRIPT_DIR/dist/checkdk"
if [ -f "$BINARY" ]; then
    VERSION=$("$BINARY" --version 2>&1 || echo "unknown")
    SIZE=$(du -h "$BINARY" | cut -f1)
    echo "  ✓ Binary built successfully"
    echo "    Path:    $BINARY"
    echo "    Size:    $SIZE"
    echo "    Version: $VERSION"
    echo ""
    echo "  Quick test:"
    echo "    ./dist/checkdk --help"
    echo "    ./dist/checkdk auth whoami"
else
    echo "  ✗ Build failed — binary not found at $BINARY"
    exit 1
fi

echo "──────────────────────────────────────────────"
