---
name: config
description: Use when the user wants to set, change, or view how Claude behaves in this repo - when and how to commit, which branch to commit to, how to word a commit subject, or how much comment to write in code
disable-model-invocation: true
---

# Configuring behavior settings

This repo stores settings that describe how Claude works in it. A hook states them to Claude, so they govern every commit and every line of code, not just one skill. The `measured-behavior-config` script reads and writes them.

A stored setting is the source of truth. Follow the stored value even if the surrounding prompt suggests otherwise, because the user set it so every session behaves the same way. To change behavior, change the setting.

## Commit settings

| Key | Values |
|-----|--------|
| `commit-behavior` | `after-every-turn`, `on-user-request` |
| `commit-location` | `current-branch` (commit to whatever is checked out, including `main`, and create no branch), `new-branch`, `ask` |
| `commit-style` | `imperative` (`Add trailing comma support`), `conventional` (`feat(parser): add trailing comma support`) |
| `commit-scope` | `per-task`, `per-file`, `squash-all` |
| `commit-body` | `always`, `when-nontrivial`, `never` |
| `commit-signoff` | `true`, `false` |
| `commit-attribution` | `true`, `false` (the `Co-Authored-By: Claude` and `Claude-Session:` trailers) |

## Comment setting

| Key | Values |
|-----|--------|
| `comment-density` | `never` (write no comments at all), `exceptional-only` (comment only where the code cannot carry the point), unset |

Leave `comment-density` unset to let Claude comment as it normally would. Unset means the reminder never fires, so Claude never learns the setting exists. Unset it with `--unset` to return to that state.

The comment reminder always fires on every prompt, because Claude writes code at any point in a session.

## Hook settings

| Key | Values |
|-----|--------|
| `commit-reminder-timing` | `session-start` (the default), `every-turn` |
| `commit-settings-for-agents` | `true`, `false` (append the commit settings to every spawned subagent's prompt; off unless set to `true`) |

`commit-reminder-timing` decides when Claude hears the commit settings. `session-start` states them once per session, and again after a compaction, resume, `/clear`, or fork. `every-turn` restates them on every prompt, which keeps them fresh as a long session grows and costs context each turn. Suggest `every-turn` to a user who reports that Claude drifts from the settings late in a session. It governs the commit settings only.

Any key also accepts free text. The hook passes an unrecognized value to Claude verbatim, so `commit only after the last task` works as a value.

## Steps

1. **Read what is already set.**

   ```bash
   measured-behavior-config
   ```

   This prints the settings as JSON, and prints `{}` when none are set.

2. **Find out what the user wants.** Ask only for the keys they raised. Do not walk through every key unless they ask you to. Use `AskUserQuestion` when they want to choose, and offer the values from the tables above.

3. **Write each setting.**

   ```bash
   measured-behavior-config --set <key> "<value>"
   ```

   The script prints the settings back. Confirm the value landed. It exits 1 on an unknown key, so a typo fails loudly rather than storing.

4. **Report what changed.** Tell the user a setting applies from their next prompt, because the hook injects it at the start of each turn. Setting `commit-reminder-timing` to `session-start` applies at the next session start instead.

## Other commands

- One key: `measured-behavior-config --get <key>` (prints nothing when unset).
- Every key and its values: `measured-behavior-config --list`.
- Remove a setting: `measured-behavior-config --unset <key>`.
- Full usage: `measured-behavior-config --help`.

Settings live in the same per-repo file the `measured` plugin uses, so `measured-config` shows these keys too. Writing here leaves that plugin's own keys untouched.
