---
name: commit-settings
description: Use when the user wants to set, change, or view how Claude commits in this repo - when to commit, which branch to commit to, or how to word a commit subject
disable-model-invocation: false
---

# Configuring commit settings

This repo stores eight settings that describe how Claude commits in it. The `commit-settings` hook states them to Claude at the start of every turn, so they govern every commit in the repo, not just one skill. The `measured-behavior-config` script reads and writes them.

A stored setting is the source of truth. Follow the stored value even if the surrounding prompt suggests otherwise, because the user set it so every session behaves the same way. To change behavior, change the setting.

## Settings

| Key | Values |
|-----|--------|
| `commit-behavior` | `after-every-turn`, `on-user-request` |
| `commit-location` | `current-branch` (commit to whatever is checked out, including `main`, and create no branch), `new-branch`, `ask` |
| `commit-style` | `imperative` (`Add trailing comma support`), `conventional` (`feat(parser): add trailing comma support`) |
| `commit-scope` | `per-task`, `per-file`, `squash-all` |
| `commit-body` | `always`, `when-nontrivial`, `never` |
| `commit-signoff` | `true`, `false` |
| `commit-attribution` | `true`, `false` (the `Co-Authored-By: Claude` and `Claude-Session:` trailers) |
| `commit-settings-for-agents` | `true`, `false` (append these settings to every spawned subagent's prompt; off unless set to `true`) |

Any key also accepts free text. The hook passes an unrecognized value to Claude verbatim, so `commit only after the last task` works as a value.

## Steps

1. **Read what is already set.**

   ```bash
   measured-behavior-config
   ```

   This prints the commit settings as JSON, and prints `{}` when none are set.

2. **Find out what the user wants.** Ask only for the keys they raised. Do not walk through all eight unless they ask you to. Use `AskUserQuestion` when they want to choose, and offer the values from the table above.

3. **Write each setting.**

   ```bash
   measured-behavior-config --set <key> "<value>"
   ```

   The script prints the commit settings back. Confirm the value landed. It exits 1 on an unknown key, so a typo fails loudly rather than storing.

4. **Report what changed.** Tell the user the settings apply from their next prompt, because the hook injects them at the start of each turn.

## Other commands

- One key: `measured-behavior-config --get <key>` (prints nothing when unset).
- Every key and its values: `measured-behavior-config --list`.
- Remove a setting: `measured-behavior-config --unset <key>`.
- Full usage: `measured-behavior-config --help`.

Settings live in the same per-repo file the `measured` plugin uses, so `measured-config` shows these keys too. Writing here leaves that plugin's own keys untouched.
