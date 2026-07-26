#!/usr/bin/env python3
"""SessionStart hook: state this repo's commit settings once a session.

A repo that sets `commit-reminder-timing` to `session-start` wants the commit
settings stated once rather than on every prompt. This hook states them, and
`reminders-every-turn.py` skips them. Exactly one of the two speaks, so the
settings never arrive twice.

Stating them once costs less context than stating them every turn. It also
fades: the settings sit at the top of a long session and a later prompt may
outweigh them. The every-turn default exists for that reason, and this hook
serves the repo that would rather spend the context elsewhere.

The hook re-fires on `resume`, `clear`, and `compact`, the moments prior
context is dropped or summarized away, so the settings return each time.

Reads the working directory from the hook payload on stdin. Prints nothing
when the repo uses the every-turn default or stores no commit setting.

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
