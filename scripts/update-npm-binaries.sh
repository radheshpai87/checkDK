#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Copy the built PyInstaller binary into the correct npm platform package.
#
# Must be run AFTER building the binary:
#   cd cli && ./build.sh
#
# Usage:
#   ./scripts/update-npm-binaries.sh
#
# This only updates the package for the CURRENT platform (the one you're on).
# To update all platforms, run this on each OS/arch (or use CI).
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BINARY="$REPO_ROOT/cli/dist/checkdk"

echo "──────────────────────────────────────────────"
echo "  Update npm platform binary"
echo "──────────────────────────────────────────────"
echo ""

# ── Check for binary ─────────────────────────────────────────────────────────
if [ ! -f "$BINARY" ]; then
    echo "  ✗ Binary not found at: $BINARY"
    echo "    Run 'cd cli && ./build.sh' first."
    exit 1
fi

# ── Detect platform ──────────────────────────────────────────────────────────
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
    x86_64)  ARCH="x64"  ;;
    aarch64) ARCH="arm64" ;;
    arm64)   ARCH="arm64" ;;
    *)
        echo "  ✗ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    linux)  PLATFORM="linux"  ;;
    darwin) PLATFORM="darwin" ;;
    *)
        echo "  ✗ Unsupported OS: $OS"
        exit 1
        ;;
esac

PKG_NAME="@checkdk/cli-${PLATFORM}-${ARCH}"
PKG_DIR="$REPO_ROOT/npm/$PKG_NAME"

if [ ! -d "$PKG_DIR" ]; then
    echo "  ✗ Package directory not found: $PKG_DIR"
    exit 1
fi

echo "  Platform:  ${PLATFORM}-${ARCH}"
echo "  Package:   ${PKG_NAME}"
echo ""

# ── Copy binary ──────────────────────────────────────────────────────────────
BIN_DIR="$PKG_DIR/bin"
mkdir -p "$BIN_DIR"
cp "$BINARY" "$BIN_DIR/checkdk"
chmod +x "$BIN_DIR/checkdk"

SIZE=$(du -h "$BIN_DIR/checkdk" | cut -f1)
echo "  → Copied binary ($SIZE) to:"
echo "    $BIN_DIR/checkdk"
echo ""

# ── Verify ───────────────────────────────────────────────────────────────────
echo "  → Verifying binary..."
if "$BIN_DIR/checkdk" --help > /dev/null 2>&1; then
    echo "    ✓ --help works"
else
    echo "    ✗ --help failed"
    exit 1
fi

VERSION=$("$BIN_DIR/checkdk" --version 2>&1 || echo "unknown")
echo "    ✓ Version: $VERSION"

# ── Show current npm package version ─────────────────────────────────────────
PKG_VERSION=$(grep '"version"' "$PKG_DIR/package.json" | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
MAIN_VERSION=$(grep '"version"' "$REPO_ROOT/npm/@checkdk/cli/package.json" | head -1 | sed 's/.*: *"\(.*\)".*/\1/')

echo ""
echo "  npm package versions:"
echo "    ${PKG_NAME}:  ${PKG_VERSION}"
echo "    @checkdk/cli:            ${MAIN_VERSION}"
echo ""

if [ "$PKG_VERSION" != "$MAIN_VERSION" ]; then
    echo "  ⚠  Version mismatch! Make sure both match before publishing."
fi

echo "──────────────────────────────────────────────"
echo ""
echo "  Next steps:"
echo "    cd $REPO_ROOT/npm/@checkdk/cli"
echo "    npm publish --access public"
echo ""
echo "    cd $PKG_DIR"
echo "    npm publish --access public"
echo "──────────────────────────────────────────────"
