#!/usr/bin/env python3
"""PreToolUse hook: give a spawned subagent this repo's commit settings.

The `commit-settings.py` hook injects the settings on every user prompt, but a
subagent never sees a user prompt. It gets a prompt written by the agent that
spawned it, so the repo's commit policy stops at the subagent boundary. This
hook appends the settings to that prompt, so an agent that commits does it the
way the repo asked.

Rewriting another agent's prompt is intrusive, so the repo opts in:

    measured-behavior-config --set commit-settings-for-agents true

The hook does nothing unless that key is true, and nothing when no commit
settings are stored.

`updatedInput` replaces the whole tool input, so this hook copies every field
it received and changes only `prompt`. Dropping a field here would silently
strip `subagent_type` or `model` from the spawn.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a subagent from spawning.
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import commit_settings  # noqa: E402
import settings_store  # noqa: E402

PROMPT_FIELD = "prompt"


def updated_prompt(prompt, reminder):
    """Return the subagent prompt with the commit settings appended."""
    return f"{prompt}\n\n{reminder}" if prompt else reminder


def decide(tool_input, settings):
    """Return the replacement tool input, or None to leave the spawn alone."""
    if not commit_settings.forward_to_agents(settings):
        return None

    reminder = commit_settings.render(settings)
    if not reminder:
        return None  # Nothing configured to forward.

    # Copy every field: updatedInput replaces the whole object.
    updated = dict(tool_input)
    updated[PROMPT_FIELD] = updated_prompt(tool_input.get(PROMPT_FIELD, ""), reminder)
    return updated


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # No parseable input -> no decision.

    tool_input = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd") or os.getcwd()

    updated = decide(tool_input, settings_store.load_settings(cwd))
    if updated is None:
        return  # Stay silent; the spawn proceeds untouched.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": updated,
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a subagent from spawning.
        sys.exit(0)
