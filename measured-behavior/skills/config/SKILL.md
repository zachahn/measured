---
name: config
description: Use when the user wants to set, change, or view how Claude behaves - when and how to commit, which branch to commit to, how to word a commit subject, or how much comment to write in code
disable-model-invocation: true
---

# Configuring behavior settings

The behavior settings describe how Claude works. A hook states them to Claude, so they govern every commit and every line of code, not just one skill. The `measured-behavior-config` script reads and writes them.

A stored setting is the source of truth. Follow the stored value even if the surrounding prompt suggests otherwise, because the user set it so every session behaves the same way. To change behavior, change the setting.

Two scopes hold settings:

- **global**, written with `--global`, applies to every project.
- **repo**, written with no scope flag, applies to this working directory and overrides the global value key by key.

Unsetting a repo key returns it to the global value. That is why a key inheriting a global value must never be written into the repo file: the copy stops tracking the global and later changes to it never reach this repo.

Run `measured-behavior-config --list` for the key and value list; it always matches what the script accepts. Run `measured-behavior-config --help` for what each key controls.

`commit-reminder-timing` governs the commit settings only, not the comment setting, which always fires on every prompt. Suggest `every-turn` to a user who reports that Claude drifts from the commit settings late in a session; `session-start` is the default and costs less context.

## Steps

1. **Ask which scope to write.** One `AskUserQuestion` before anything else:

   ```json
   {
     "question": "Where should these settings apply?",
     "header": "Scope",
     "multiSelect": false,
     "options": [
       { "label": "Every project", "description": "Store them globally. Every repo inherits them, and any repo can override a single key later." },
       { "label": "This repo only", "description": "Store them for this working directory. They override the global values for the keys you set." }
     ]
   }
   ```

   Every write in this run uses the scope from this answer. `--global` for every project, no flag for this repo only.

2. **Read both scopes.**

   ```bash
   measured-behavior-config --global
   measured-behavior-config --repo
   ```

   Each prints JSON, and prints `{}` when that scope holds nothing. Keep both open. Which file holds a value decides what each question says and what accepting it writes.

3. **Ask about every key.** Walk every key from `measured-behavior-config --list`, not only the ones the user raised. Use `AskUserQuestion`, batching 4 keys per call.

   State the key's current value in the question, and name where it comes from:

   - in the repo file: `Currently: imperative, set in this repo.`
   - in the global file only: `Currently: imperative, inherited from your global settings.`
   - in neither: `Currently: unset.`

   For a global run, read `Currently:` from the global file alone and ignore the repo file.

   Build the options like this, for a repo run of `commit-style` that inherits `imperative`:

   ```json
   {
     "question": "How should Claude word a commit subject? Currently: imperative, inherited from your global settings.",
     "header": "Style",
     "multiSelect": false,
     "options": [
       { "label": "conventional", "description": "Prefix the subject with a type, such as feat: or fix:. Writes a repo value that overrides your global one." },
       { "label": "imperative", "description": "Write the subject as an imperative sentence, with no type prefix. Writes a repo value that stays imperative even if you change your global setting later." },
       { "label": "Use global (imperative) (current)", "description": "Store nothing here and follow your global setting, including any later change to it." }
     ]
   }
   ```

   Take the value labels and descriptions from `--list`. The last option is always one of these three, and each one runs an unset:

   - repo run, a global value exists: `Use global (<value>)`
   - repo run, no global value: `None`
   - global run: `None`

   Mark exactly one option `(current)`. For an inherited key that is the `Use global` option, never the value option that matches it. Picking the matching value writes a repo override that equals the global today and stops following it tomorrow; picking `Use global` keeps the key inherited. The two do different things, so mark only the one that describes the current state.

   The tool caps a question at 4 options. Add a `Skip` option only when the values plus the unset option leave room, which means only for a key with two known values.

4. **Write each answer.**

   ```bash
   measured-behavior-config --set <key> "<value>"           # this repo only
   measured-behavior-config --global --set <key> "<value>"  # every project
   ```

   The script prints the settings back. Confirm the value landed. It exits 1 on an unknown key, so a typo fails loudly rather than storing.

   For `Use global` or `None`, run `--unset <key>` with the same scope flag. For `Skip`, run nothing.

5. **Report what changed.** Tell the user a setting applies from their next prompt, because the hook injects it at the start of each turn. Setting `commit-reminder-timing` to `session-start` applies at the next session start instead.

   After a global run, compare what you wrote against step 2's `--repo` output. Name any key the repo also sets, because that repo value keeps winning over the global one you just wrote, and give the user the command that clears it:

   ```bash
   measured-behavior-config --unset <key>
   ```

## Other commands

- One key in force: `measured-behavior-config --get <key>` (prints nothing when unset).
- One key in one scope: `measured-behavior-config --global --get <key>` or `--repo --get <key>`.
- Every key and its values: `measured-behavior-config --list`.
- Everything in force: `measured-behavior-config` with no arguments, which merges both scopes.
- Full usage: `measured-behavior-config --help`.

The repo file is shared with the `measured` plugin, so `measured-config` shows these keys too. Writing here leaves that plugin's own keys untouched. The global file belongs to this plugin alone.
