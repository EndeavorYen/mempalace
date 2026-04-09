#!/bin/bash
# MemPalace Fork — One-click Update
# https://github.com/EndeavorYen/mempalace
#
# Usage:  bash update.sh

set -euo pipefail

INSTALL_DIR="${MEMPALACE_INSTALL_DIR:-$HOME/.mempalace-fork}"

echo "╔═══════════════════════════════════════════╗"
echo "║  MemPalace (EndeavorYen fork) — Update    ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── 1. Check install exists ────────────────────────────────
if [ ! -d "$INSTALL_DIR/.git" ]; then
    echo "✗ No install found at $INSTALL_DIR"
    echo "  Run install.sh first."
    exit 1
fi

OLD_VERSION=$(python3 -c 'from mempalace import __version__; print(__version__)' 2>/dev/null || echo '?')
OLD_COMMIT=$(git -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || echo '?')

# ── 2. Pull latest ─────────────────────────────────────────
echo "→ Pulling latest from origin/main..."
git -C "$INSTALL_DIR" fetch origin main
git -C "$INSTALL_DIR" merge origin/main --ff-only || {
    echo "✗ Fast-forward merge failed. You may have local changes."
    echo "  Resolve manually: cd $INSTALL_DIR && git status"
    exit 1
}

NEW_COMMIT=$(git -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || echo '?')

if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
    echo "  Already up to date ($OLD_COMMIT)."
    exit 0
fi

# ── 3. Reinstall package ──────────────────────────────────
echo "→ Reinstalling Python package..."
pip install -e "$INSTALL_DIR" --quiet 2>/dev/null || pip3 install -e "$INSTALL_DIR" --quiet 2>/dev/null
pip install -e "$INSTALL_DIR[multilingual]" --quiet 2>/dev/null || true

NEW_VERSION=$(python3 -c 'from mempalace import __version__; print(__version__)' 2>/dev/null || echo '?')

# ── Done ───────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  Update complete!                         ║"
echo "╠═══════════════════════════════════════════╣"
echo "║  $OLD_VERSION ($OLD_COMMIT) → $NEW_VERSION ($NEW_COMMIT)"
echo "╚═══════════════════════════════════════════╝"
