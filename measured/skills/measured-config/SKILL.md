---
name: measured-config
description: Use when the user wants to set, change, or view this repo's measured settings - such as the setup commands a new git worktree should run
disable-model-invocation: true
---

# Configuring Measured

Measured keeps a few per-repo settings outside the repo, shared across every Claude session in it. The `measured-config` script reads and writes them.

## Settings

| Key | Holds |
|-----|-------|
| `worktree-setup` | Shell commands that prepare a fresh worktree to work in (install deps, build, etc.). The **using-git-worktrees** skill runs these after creating a worktree. |

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
