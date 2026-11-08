---
name: config
description: Use when the user wants to set, change, or view this repo's "measured" settings
disable-model-invocation: false
---

# Configuring Measured

Measured stores a few settings for each repo. The settings live outside the repo and are shared by every Claude session in that repo. Read and write settings with the `measured-config` script.

A stored setting is the source of truth. Follow any value from `measured-config --get`, even if the prompt says otherwise. The user set the value deliberately so every session behaves the same way. To change the behavior, change the setting.

## Settings

| Key | Value |
|-----|-------|
| `docs-location` | Where to store plan docs (ARCHITECTURE.md, TICKET.md): `XDG_STATE_HOME` for the default state directory, or `REPO: <path/to/docs>` for a directory inside the repo. |

## Behavior settings

These settings control how Claude commits and writes code comments in this repo. The **measured-settings** plugin manages them, and its hook adds each set value to Claude's context. Unset settings leave Claude's default behavior unchanged.

Set these with `measured-settings-config --set <key> <value>`, which rejects unknown keys. Both commands share one settings file.

| Key | Value |
|-----|-------|
| `commit-behavior` | When to commit: `after-every-turn` or `on-user-request`. |
| `commit-location` | Which branch to commit to. `current-branch`: commit to the checked-out branch, even `main`, and never create or suggest a new branch. `new-branch`: create a new branch for the work. `ask`: ask once per session. |
| `commit-style` | How to write the subject line: `imperative` (`Add trailing comma support`) or `conventional` (`feat(parser): add trailing comma support`). |
| `commit-scope` | How much work goes into each commit: `per-task`, `per-file`, or `squash-all`. |
| `commit-body` | When to write a commit body: `always`, `when-nontrivial`, or `never`. |
| `commit-reminder-timing` | How often to remind Claude of the commit settings. `session-start` (default): once per session, and again after a compaction, resume, or fork. `every-turn`: on every prompt. |
| `comment-density` | How many code comments to write. `never`: no comments at all. `exceptional-only`: comments only where the code alone is not clear enough. Unset: Claude comments as usual. |

Each setting also accepts free text when no listed value fits, such as `measured-settings-config --set commit-behavior "commit only after the last task"`. Claude receives the text verbatim.

## Steps

1. **Find out what to set.** If the user gave no value, ask for one.

2. **Save the setting.**

   ```bash
   measured-config --set <key> "<value>"
   ```

   For a behavior setting, use `measured-settings-config --set` instead. Check that the new value appears in the printed settings.

3. **Read settings when asked.**

   - One key: `measured-config --get <key>`. Prints nothing if the key is unset.
   - All settings: `measured-config` with no arguments.

4. **Remove a setting** with `measured-config --unset <key>`.

Run `measured-config --help` for full usage.
