---
name: config
description: Use when the user wants to set, change, or view how Claude behaves in this repo - when and how to commit, which branch to commit to, how to word a commit subject, or how much comment to write in code
disable-model-invocation: true
---

# Configuring behavior settings

This repo stores settings that describe how Claude works in it. A hook states them to Claude, so they govern every commit and every line of code, not just one skill. The `measured-behavior-config` script reads and writes them.

A stored setting is the source of truth. Follow the stored value even if the surrounding prompt suggests otherwise, because the user set it so every session behaves the same way. To change behavior, change the setting.

Run `measured-behavior-config --list` for the key and value list; it always matches what the script accepts. Run `measured-behavior-config --help` for what each key controls.

`commit-reminder-timing` governs the commit settings only, not the comment setting, which always fires on every prompt. Suggest `every-turn` to a user who reports that Claude drifts from the commit settings late in a session; `session-start` is the default and costs less context.

## Steps

1. **Read what is already set.**

   ```bash
   measured-behavior-config
   ```

   This prints the settings as JSON, and prints `{}` when none are set. Keep this open to compare against as you go.

2. **List every key and its values.**

   ```bash
   measured-behavior-config --list
   ```

   This prints every key together with the values it accepts.

3. **Ask about every key.** Walk through every key from step 2's `--list` output, not only the ones the user raised. Use `AskUserQuestion`, batching up to 4 keys per call, since the tool accepts at most 4 questions per call. For each key, offer its listed values plus a `None` option meaning "leave this key unset." If step 1 showed a stored value for the key, name it in the question so the user knows what they would be changing.

4. **Write each answer.**

   ```bash
   measured-behavior-config --set <key> "<value>"
   ```

   The script prints the settings back. Confirm the value landed. It exits 1 on an unknown key, so a typo fails loudly rather than storing.

   For a key the user answered `None`, leave it unset instead: run `measured-behavior-config --unset <key>` if step 1 showed it already had a value, otherwise do nothing.

5. **Report what changed.** Tell the user a setting applies from their next prompt, because the hook injects it at the start of each turn. Setting `commit-reminder-timing` to `session-start` applies at the next session start instead.

## Other commands

- One key: `measured-behavior-config --get <key>` (prints nothing when unset).
- Every key and its values: `measured-behavior-config --list`.
- Remove a setting: `measured-behavior-config --unset <key>`.
- Full usage: `measured-behavior-config --help`.

Settings live in the same per-repo file the `measured` plugin uses, so `measured-config` shows these keys too. Writing here leaves that plugin's own keys untouched.
