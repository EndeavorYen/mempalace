---
name: save
description: Save a session checkpoint to mempalace before clearing context. Use when the user says "/save", "save checkpoint", "save session", or before clearing.
---

# Save Session Checkpoint

Save the current session's state to mempalace so it can be restored after `/clear`.

## What to do

1. **Introspect the current session** — determine:
   - What project you're working on (infer from cwd, git repo name, or ask)
   - What task you're currently doing
   - What's done and what's remaining (progress checklist)
   - Key decisions made and why
   - What topics have relevant memories in mempalace (memory triggers)
   - What to do next when resuming

2. **Call the MCP tool:**
   ```
   session_checkpoint(
     project: "<project-name>",
     current_task: "<what you're working on>",
     progress: "- [x] done items\n- [ ] remaining items",
     decisions: "<key decisions and rationale>",
     memory_triggers: "- <keyword for mempalace search>\n- <another keyword>",
     next_steps: "<what to do when resuming>"
   )
   ```

3. **Confirm to the user** what was saved and the token estimate.

## Guidelines

- Be thorough but concise — every token in state.md costs tokens on restore
- Focus on decisions and rationale (the "why") — code changes are in git
- Memory triggers should be specific search queries, not generic topics
- If unsure about the project name, use the git repo name or cwd basename
