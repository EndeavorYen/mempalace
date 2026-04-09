#!/bin/bash
# MemPalace SessionStart Hook — auto-inject wake-up context
# All logic lives in mempalace.hooks_cli for cross-harness extensibility
INPUT=$(cat)
echo "$INPUT" | python3 -m mempalace hook run --hook session-start --harness claude-code
