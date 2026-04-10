---
name: save-clear
description: Save session checkpoint then clear context. Use when the user says "/save-clear", "save and clear", "checkpoint and clear", or wants to reset context while preserving state.
---

# Save and Clear

Save the current session's state to mempalace, then clear context to free tokens.

## What to do

1. **Run the /save flow first** — archive knowledge, then checkpoint:
   - Archive key decisions and feedback as individual drawers (mempalace_add_drawer)
   - Save structured facts as KG triples (mempalace_kg_add)
   - Write a diary summary (mempalace_diary_write)
   - Finally, call `session_checkpoint(...)` with task state and progress

2. **Confirm the save succeeded** — show the user:
   - What was saved
   - Token estimate
   - State file path

3. **Tell the user to clear:**
   ```
   Checkpoint saved. To clear context and free tokens, type: /clear
   After clearing, type: /restore to pick up where you left off.
   ```

## Why not auto-clear?

`/clear` is a built-in Claude Code command that cannot be triggered programmatically from a skill. The user must type it manually. This is actually a feature — it gives the user a chance to verify the checkpoint before clearing.

## Quick reference for the user

```
/save-clear  →  saves checkpoint, prompts you to /clear
/clear       →  clears context (built-in)
/restore     →  loads checkpoint + wake-up (~1100-1300 tokens)
```
