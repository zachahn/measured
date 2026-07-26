#!/usr/bin/env python3
"""UserPromptSubmit hook: state this repo's commit settings each turn.

A repo stores how it wants commits made: whether to commit unprompted, how to
word a subject line, whether to sign off. A SessionStart hook states that once
and it fades as the session grows, so this hook fires on every prompt and the
settings ride in fresh each turn.

The reminder reaches Claude only. UserPromptSubmit hooks add to context through
`hookSpecificOutput.additionalContext`, which the user never sees, so a repo
with no commit settings stored prints nothing and costs the user nothing.

Reads the working directory from the hook payload on stdin. Prints nothing when
no commit setting is set.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a prompt.
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import commit_settings  # noqa: E402
import settings_store  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()

    reminder = commit_settings.render(settings_store.load_settings(cwd))
    if not reminder:
        return  # Nothing configured; stay quiet.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": reminder,
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
