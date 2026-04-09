#!/bin/bash
# Auto-install mempalace if not available, then run the MCP server.
# Used by Claude Code plugin to ensure pip dependency is met.
if ! python3 -c "import mempalace" 2>/dev/null; then
    pip install mempalace --quiet 2>/dev/null || pip3 install mempalace --quiet 2>/dev/null || true
fi
exec python3 -m mempalace.mcp_server "$@"
