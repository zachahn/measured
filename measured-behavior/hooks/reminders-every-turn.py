#!/usr/bin/env python3
"""UserPromptSubmit hook: state this repo's behavior settings each turn.

A SessionStart hook states a setting once and it fades as the session grows.
This hook fires on every prompt, so a setting rides in fresh each turn.

Two reminders can appear here. The comment setting always does, because Claude
writes code at any point in a session and the setting governs every line of it.
The commit settings appear only when the repo sets `commit-reminder-timing` to
`every-turn`. They default to once a session, which
`reminders-session-start.py` handles.

The reminders reach Claude only. UserPromptSubmit hooks add to context through
`hookSpecificOutput.additionalContext`, which the user never sees, so a repo
with no settings stored prints nothing and costs the user nothing.

Reads the working directory from the hook payload on stdin.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a prompt.
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import behavior_settings  # noqa: E402
import settings_store  # noqa: E402


def reminders(settings):
    """Return the reminders this hook states, in the order Claude reads them."""
    parts = []
    if behavior_settings.commit_timing(settings) == behavior_settings.EVERY_TURN:
        parts.append(behavior_settings.render(settings))
    parts.append(behavior_settings.render_comment(settings))
    return [part for part in parts if part]


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()

    parts = reminders(settings_store.load_settings(cwd))
    if not parts:
        return  # Nothing configured; stay quiet.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(parts),
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a prompt.
        sys.exit(0)
