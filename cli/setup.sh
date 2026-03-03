#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# checkDK CLI – one-shot setup script
#
# Usage:
#   cd cli
#   bash setup.sh
#
# After setup:
#   source .venv/bin/activate
#   checkdk --help
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

PYTHON=${PYTHON:-python3}
VENV_DIR=".venv"

echo "─────────────────────────────────────"
echo " checkDK CLI setup"
echo "─────────────────────────────────────"

# 1. Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "→ Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
else
    echo "→ Virtual environment already exists, skipping creation."
fi

# 2. Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 3. Upgrade pip silently
pip install --quiet --upgrade pip

# 4. Install the CLI package in editable mode
echo "→ Installing checkdk-cli..."
pip install --quiet -e .

echo ""
echo "✓ Done! Activate the environment with:"
echo ""
echo "    source cli/.venv/bin/activate"
echo ""
echo "Then configure the backend URL (only needed once):"
echo ""
echo "    export CHECKDK_API_URL=http://localhost:8000"
echo "    # or run:  checkdk init"
echo ""
echo "Usage examples:"
echo "    checkdk docker compose up -d"
echo "    checkdk kubectl apply -f deployment.yaml"
echo "    checkdk predict --cpu 93 --memory 91"
echo ""
