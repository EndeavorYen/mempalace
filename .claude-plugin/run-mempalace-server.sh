#!/bin/bash
# Auto-install mempalace if not available, then run the MCP server.
# Used by Claude Code plugin to ensure pip dependency is met.
#
# Installs from the fork repo (editable) rather than PyPI,
# so users get multilingual + session + token-optimized features.
if ! python3 -c "import mempalace" 2>/dev/null; then
    PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"
    if [ -f "$REPO_ROOT/setup.py" ] || [ -f "$REPO_ROOT/pyproject.toml" ]; then
        pip install -e "$REPO_ROOT" --quiet 2>/dev/null || pip3 install -e "$REPO_ROOT" --quiet 2>/dev/null || true
    else
        pip install "mempalace @ git+https://github.com/EndeavorYen/mempalace.git" --quiet 2>/dev/null || \
        pip3 install "mempalace @ git+https://github.com/EndeavorYen/mempalace.git" --quiet 2>/dev/null || true
    fi
fi
exec python3 -m mempalace.mcp_server "$@"
