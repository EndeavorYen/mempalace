#!/bin/bash
# MemPalace Fork — One-click Uninstall
# https://github.com/EndeavorYen/mempalace
#
# Usage:  bash uninstall.sh [--purge]
#
# By default, keeps your palace data (~/.mempalace/).
# Use --purge to remove everything including stored memories.

set -euo pipefail

INSTALL_DIR="${MEMPALACE_INSTALL_DIR:-$HOME/.mempalace-fork}"
MCP_NAME="mempalace"
PURGE=false

for arg in "$@"; do
    case "$arg" in
        --purge) PURGE=true ;;
    esac
done

echo "╔═══════════════════════════════════════════╗"
echo "║  MemPalace (EndeavorYen fork) — Uninstall ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── 1. Remove MCP server registration ─────────────────────
echo "→ Removing MCP server..."
if command -v claude &>/dev/null; then
    claude mcp remove "$MCP_NAME" 2>/dev/null && echo "  MCP server removed ✓" || echo "  (not registered)"
else
    echo "  (Claude Code CLI not found, skipping)"
fi

# ── 2. pip uninstall ───────────────────────────────────────
echo "→ Uninstalling Python package..."
pip uninstall mempalace -y 2>/dev/null || pip3 uninstall mempalace -y 2>/dev/null || echo "  (not installed via pip)"
echo "  pip package removed ✓"

# ── 3. Remove cloned repo ─────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    echo "→ Removing source at $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
    echo "  Source removed ✓"
else
    echo "→ No source directory found at $INSTALL_DIR"
fi

# ── 4. Optionally remove palace data ──────────────────────
if [ "$PURGE" = true ]; then
    echo "→ Purging palace data at ~/.mempalace/..."
    if [ -d "$HOME/.mempalace" ]; then
        rm -rf "$HOME/.mempalace"
        echo "  Palace data removed ✓"
    else
        echo "  (no palace data found)"
    fi
else
    echo ""
    echo "  ℹ Palace data preserved at ~/.mempalace/"
    echo "    To remove all memories: bash uninstall.sh --purge"
fi

# ── Done ───────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  Uninstall complete.                      ║"
echo "╚═══════════════════════════════════════════╝"
