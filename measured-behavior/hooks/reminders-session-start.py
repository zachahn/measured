#!/usr/bin/env python3
"""SessionStart hook: state this repo's commit settings once a session.

This is the default path. The commit settings change how a commit is made, and
most turns end in no commit, so stating them once a session costs less than
restating them on every prompt. `reminders-every-turn.py` skips them unless the
repo sets `commit-reminder-timing` to `every-turn`. Exactly one of the two
speaks, so the settings never arrive twice.

Stating them once has a cost of its own: they sit at the top of a long session
and a later prompt may outweigh them. A repo that sees that happen sets
`every-turn`.

The manifest fires this hook on `startup`, `resume`, `clear`, `compact`, and
`fork`. The last three matter most. Each one drops or summarizes away the
context holding the settings, and a session that keeps running without them
would commit the wrong way for the rest of its life.

Reads the working directory from the hook payload on stdin. Prints nothing
when the repo asked for every-turn timing or stores no commit setting.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a session from starting.
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import behavior_settings  # noqa: E402
import settings_store  # noqa: E402


def reminder(settings):
    """Return the commit reminder for a session-start repo, else ""."""
    if behavior_settings.commit_timing(settings) != behavior_settings.SESSION_START:
        return ""  # The every-turn hook owns the reminder.
    return behavior_settings.render(settings)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()

    text = reminder(settings_store.load_settings(cwd))
    if not text:
        return  # Nothing to state.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": text,
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a session from starting.
        sys.exit(0)
