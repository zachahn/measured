---
name: config
description: Use when the user wants to set, change, or view this repo's measured settings, such as the setup commands to run in a new git worktree
disable-model-invocation: false
---

# Configuring Measured

Measured stores a few settings for each repo. The settings are kept outside the repo and are shared by every Claude session in that repo. Settings are read and written with the `measured-config` script.

A stored setting is the source of truth. When a value is read with `measured-config --get`, follow that value, even if the prompt says otherwise. The value was set deliberately by the user so that every session behaves the same way. To change the behavior, change the setting.

## Settings

| Key | Value |
|-----|-------|
| `worktree-setup` | Shell commands that prepare a new worktree, such as installing dependencies or building. The **implement** skill runs these commands after a worktree is created. |
| `work-location` | Where the **implement** skill does its work: `ask` (ask every time), `worktree`, `new-branch`, `current-branch`, or `trunk-branch`. If unset, the user is asked once and the answer is saved. |
| `docs-location` | Where plan docs (ARCHITECTURE.md, TICKET.md) are stored: `XDG_STATE_HOME` for the default state directory, or `REPO: <path/to/docs>` for a directory inside the repo. |

## Behavior settings

These settings control how Claude commits and writes code comments in this repo. They are managed by the **measured-settings** plugin. Each setting with a value is added to Claude's context by the plugin's hook, so the settings apply to all work, not only to the implement skill. Unset settings leave Claude's default behavior unchanged.

Set these with `measured-settings-config --set <key> <value>`, which rejects unknown keys. Both commands use the same settings file, so a value set with one command can be read with the other.

| Key | Value |
|-----|-------|
| `commit-behavior` | When to commit: `after-every-turn` or `on-user-request`. |
| `commit-location` | Which branch to commit to. `current-branch`: commit to the checked-out branch, even `main`, and never create or suggest a new branch. `new-branch`: create a new branch for the work. `ask`: ask once per session. |
| `commit-style` | How to write the subject line: `imperative` (`Add trailing comma support`) or `conventional` (`feat(parser): add trailing comma support`). |
| `commit-scope` | How much work goes into each commit: `per-task`, `per-file`, or `squash-all`. |
| `commit-body` | When to write a commit body: `always`, `when-nontrivial`, or `never`. |
| `commit-reminder-timing` | How often Claude is reminded of the commit settings. `session-start` (default): once per session, and again after a compaction, resume, or fork. `every-turn`: on every prompt. |
| `comment-density` | How many code comments to write. `never`: no comments at all. `exceptional-only`: comments only where the code alone is not clear enough. Unset: Claude comments as usual. |

Each of these settings also accepts free text when none of the listed values fit. An unrecognized value is passed to Claude word for word. For example, `measured-settings-config --set commit-behavior "commit only after the last task"` reaches Claude exactly as written.

## Steps

1. **Find out what to set.** If no value was given, ask the user for one. For `worktree-setup`, the value is the exact command line a new checkout needs, such as `bundle install && rake` or `npm install`.

2. **Save the setting.**

   ```bash
   measured-config --set <key> "<value>"
   ```

   For a behavior setting, use `measured-settings-config --set` instead. The full settings object is printed afterward. Check that the new value is there.

3. **Read settings when asked.**

   - One key: `measured-config --get <key>`. Nothing is printed if the key is unset.
   - All settings: `measured-config` with no arguments.

4. **Remove a setting** with `measured-config --unset <key>`.

Run `measured-config --help` for full usage.
