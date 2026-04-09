---
name: restore
description: Restore session context from mempalace after clearing. Use when the user says "/restore", "restore session", "where was I", or at the start of a new session.
---

# Restore Session Context

Restore the previous session's state from mempalace after a `/clear`.

## What to do

1. **Call the MCP tool:**
   ```
   session_restore(project: "<project-name or omit for latest>")
   ```

2. **Read the response** which contains:
   - `state`: the saved state.md (current task, progress, decisions, memory triggers)
   - `wake_up`: L0 identity + L1 essential story
   - `recent_checkpoints`: last 3 session summaries
   - `memory_triggers`: keywords for on-demand mempalace search

3. **Brief the user** on where they left off:
   - Current task and progress
   - Key decisions that were made
   - What the next steps are

4. **Keep Memory Triggers in mind** — when conversation touches one of these topics, call `mempalace_search` with the trigger keyword to pull in relevant context on demand. Do NOT pre-load all triggers — that defeats the purpose of saving tokens.

## If no state exists

If `has_state` is false, tell the user:
- No saved checkpoint found
- List available projects if any (`session_list`)
- Suggest using `/save` before their next `/clear`
