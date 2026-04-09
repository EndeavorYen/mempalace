#!/bin/bash
# MemPalace Fork — One-click Install
# https://github.com/EndeavorYen/mempalace
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/EndeavorYen/mempalace/main/install.sh | bash
#   # or from a local clone:
#   bash install.sh

set -euo pipefail

REPO_URL="https://github.com/EndeavorYen/mempalace.git"
INSTALL_DIR="${MEMPALACE_INSTALL_DIR:-$HOME/.mempalace-fork}"
MCP_NAME="mempalace"

echo "╔═══════════════════════════════════════════╗"
echo "║  MemPalace (EndeavorYen fork) — Install   ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── 1. Check dependencies ──────────────────────────────────
echo "→ Checking dependencies..."

if ! command -v python3 &>/dev/null; then
    echo "✗ python3 not found. Please install Python 3.9+."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "✗ Python 3.9+ required (found $PY_VERSION)."
    exit 1
fi
echo "  python3 $PY_VERSION ✓"

if ! command -v git &>/dev/null; then
    echo "✗ git not found. Please install git."
    exit 1
fi
echo "  git ✓"

# ── 2. Clone or update repo ────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "→ Updating existing install at $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --ff-only origin main 2>/dev/null || {
        echo "  (pull failed, using existing version)"
    }
else
    echo "→ Cloning to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# ── 3. pip install (editable) ──────────────────────────────
echo "→ Installing Python package..."
pip install -e "$INSTALL_DIR" --quiet 2>/dev/null || pip3 install -e "$INSTALL_DIR" --quiet 2>/dev/null

# Install multilingual support (optional, skip on failure)
pip install -e "$INSTALL_DIR[multilingual]" --quiet 2>/dev/null || {
    echo "  (multilingual extras skipped — install manually with: pip install -e '$INSTALL_DIR[multilingual]')"
}

echo "  mempalace $(python3 -c 'from mempalace import __version__; print(__version__)' 2>/dev/null || echo '?') ✓"

# ── 4. Register MCP server ─────────────────────────────────
echo "→ Registering MCP server..."

if command -v claude &>/dev/null; then
    # Remove old registration if exists, then re-add
    claude mcp remove "$MCP_NAME" 2>/dev/null || true
    claude mcp add "$MCP_NAME" -- python3 -m mempalace.mcp_server
    echo "  MCP server '$MCP_NAME' registered ✓"
else
    echo "  ⚠ Claude Code CLI not found — skipping MCP registration."
    echo "    Register manually later:"
    echo "    claude mcp add mempalace -- python3 -m mempalace.mcp_server"
fi

# ── 5. Set up hooks (copy to settings if not using plugin) ─
HOOKS_SRC="$INSTALL_DIR/.claude-plugin/hooks"
echo "→ Hooks available at: $HOOKS_SRC/"
echo "  If installed as plugin, hooks are auto-configured."
echo "  For manual setup, add to ~/.claude/settings.json:"
echo ""
echo "    \"hooks\": {"
echo "      \"SessionStart\": [{\"hooks\": [{\"type\": \"command\", \"command\": \"bash $HOOKS_SRC/mempal-session-start-hook.sh\"}]}],"
echo "      \"Stop\": [{\"hooks\": [{\"type\": \"command\", \"command\": \"bash $HOOKS_SRC/mempal-stop-hook.sh\"}]}],"
echo "      \"PreCompact\": [{\"hooks\": [{\"type\": \"command\", \"command\": \"bash $HOOKS_SRC/mempal-precompact-hook.sh\"}]}]"
echo "    }"

# ── 6. Init palace if first time ──────────────────────────
if [ ! -d "$HOME/.mempalace/palace" ]; then
    echo ""
    echo "→ No palace found. Run 'mempalace init <your-project-dir>' to set up."
else
    echo ""
    echo "→ Existing palace found at ~/.mempalace/palace ✓"
fi

# ── Done ───────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  Install complete!                        ║"
echo "╠═══════════════════════════════════════════╣"
echo "║  • Source:  $INSTALL_DIR"
echo "║  • MCP:     claude mcp add mempalace      ║"
echo "║  • Verify:  mempalace status              ║"
echo "║  • Update:  bash $INSTALL_DIR/install.sh"
echo "║  • Remove:  bash $INSTALL_DIR/uninstall.sh"
echo "╚═══════════════════════════════════════════╝"
