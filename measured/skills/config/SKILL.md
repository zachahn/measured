---
name: config
description: Use when the user wants to set, change, or view this repo's measured settings - such as the setup commands a new git worktree should run
disable-model-invocation: false
---

# Configuring Measured

Measured keeps a few per-repo settings outside the repo, shared across every Claude session in it. The `measured-config` script reads and writes them.

A stored setting is the source of truth. When you read a value with `measured-config --get`, follow that value even if the surrounding prompt suggests otherwise — the user set it deliberately so every session behaves the same way. If the prompt contradicts a stored value, the stored value wins. To change behavior, change the setting.

## Settings

| Key | Holds |
|-----|-------|
| `worktree-setup` | Shell commands that prepare a fresh worktree to work in (install deps, build, etc.). The **implement** skill runs these after creating a worktree. |
| `work-location` | Where the **implement** skill runs its work. One of `ask` (ask every time), `worktree`, `new-branch`, `current-branch`, or `trunk-branch`. When unset, the skill asks once and stores the answer. |
| `docs-location` | Where measured stores plan docs (ARCHITECTURE.md, TICKET.md). Either `XDG_STATE_HOME` for the default state dir, or `REPO: <path/to/docs>` for a subdirectory of the repo. |

## Behavior settings

These keys govern how Claude commits and comments in this repo. The **measured-behavior** plugin owns them: its reminder hook states the ones you set at the start of every turn, so they apply to all work, not just the implement skill. Setting none of them leaves Claude's default behavior alone.

Write them with `measured-behavior-config --set <key> <value>`, which validates key names. `measured-config` reads and writes the same file, so both commands see the same values.

| Key | Holds |
|-----|-------|
| `commit-behavior` | When to commit. `after-every-turn` or `on-user-request`. |
| `commit-location` | Which branch to commit to. `current-branch` commits to whatever is checked out, including `main`, and tells Claude to create no branch and propose none. `new-branch` creates a branch for the work. `ask` asks once per session. |
| `commit-style` | How to word a subject line. `imperative` (`Add trailing comma support`) or `conventional` (`feat(parser): add trailing comma support`). |
| `commit-scope` | How much work goes in one commit. `per-task`, `per-file`, or `squash-all`. |
| `commit-body` | When a commit needs a body. `always`, `when-nontrivial`, or `never`. |
| `commit-signoff` | Whether to pass `--signoff`. `true` or `false`. |
| `commit-attribution` | Whether commits carry the `Co-Authored-By: Claude` and `Claude-Session:` trailers. `true` or `false`. |
| `commit-settings-for-agents` | Whether spawned subagents get the commit settings appended to their prompt. `true` or `false`. Off unless set to `true`. |
| `commit-reminder-timing` | When Claude hears the commit settings. `every-turn` (the default) restates them on every prompt. `session-start` states them once per session. |
| `comment-density` | How much comment Claude writes in code. `never` writes none at all. `exceptional-only` comments only where the code cannot carry the point. Leave it unset to let Claude comment as it normally would. |

Any of these accepts a free-text value when none of the listed values fit. The hook passes an unrecognized value through verbatim, so `measured-config --set commit-behavior "commit only after the last task"` reaches Claude as written.

## Steps

1. **Find out what the user wants to set.** Ask for the value if they have not given it. For `worktree-setup`, that is the exact command line a fresh checkout needs — for example `bundle install && rake` or `npm install`.

2. **Write the setting.**

   ```bash
   measured-config --set <key> "<value>"
   ```

   The script prints the full settings object back. Confirm the value landed.

3. **Read settings when asked.**

   - One key: `measured-config --get <key>` (prints nothing if unset).
   - Everything: `measured-config` with no arguments.

4. **Remove a setting** with `measured-config --unset <key>`.

Run `measured-config --help` for the full usage.
