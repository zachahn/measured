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
| `commit-after-task` | Whether the **implement** skill commits each task after it passes review. Prefer `true` or `false`; may also hold a free-text instruction (e.g. `commit only after the last task`) passed to the implementer. When unset, the skill asks once and stores the answer. |
| `work-location` | Where the **implement** skill runs its work. One of `ask` (ask every time), `worktree`, `new-branch`, `current-branch`, or `default-branch`. When unset, the skill asks once and stores the answer. |

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
