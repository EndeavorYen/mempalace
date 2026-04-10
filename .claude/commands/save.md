---
name: save
description: Save a session checkpoint to mempalace before clearing context. Use when the user says "/save", "save checkpoint", "save session", or before clearing.
---

# Save Session — Archive Knowledge + Checkpoint

Save the current session's knowledge and state to mempalace so it can be restored and searched later.

## What to do

### Step 1: Archive knowledge to mempalace

Before checkpointing, save the session's **knowledge** as searchable entries:

a. **Key decisions and external feedback** — save each as an individual drawer:
   ```
   mempalace_add_drawer(
     wing: "project",
     room: "<topic>",
     content: "<decision/feedback with context and rationale>"
   )
   ```
   One topic per drawer (e.g., reviewer feedback, architecture decision, bug root cause).

b. **Structured facts** — save as KG triples:
   ```
   mempalace_kg_add(subject: "...", predicate: "...", object: "...")
   ```

c. **Session diary** — write a narrative summary:
   ```
   mempalace_diary_write(
     agent_name: "<your name>",
     entry: "<what happened, what was learned>",
     topic: "<project or topic>"
   )
   ```

### Step 2: Save session checkpoint

After archiving knowledge, save the task state for `/restore`:

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

### Step 3: Confirm to the user

Report what was saved:
- Number of drawers archived
- Number of KG triples added
- Checkpoint token estimate

## Guidelines

- **Step 1 is critical** — drawers are what make knowledge searchable across sessions. Without them, only the checkpoint summary survives.
- One drawer per topic — don't dump everything into one giant drawer
- Use verbatim quotes from external feedback (PR reviews, issue comments) where possible
- Be thorough but concise — every token in state.md costs tokens on restore
- Focus on decisions and rationale (the "why") — code changes are in git
- Memory triggers should be specific search queries that match your drawer content
- If unsure about the project name, use the git repo name or cwd basename
