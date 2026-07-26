#!/usr/bin/env python3
"""SessionStart hook: offer commit settings when the repo has none.

The `commit-settings.py` hook states this repo's commit settings on every
prompt, but only once someone has set them. A repo that has never set them gets
no signal that the settings exist, so this hook prints a short setup message at
the start of a session.

The message reaches the user, not Claude. A SessionStart hook's stdout becomes
Claude's context, so this hook writes to stderr, which Claude Code shows in the
user's terminal instead. Claude needs no instruction here: unset settings mean
"behave normally", and describing a feature the user has not opted into would
just spend context. The hook prints nothing once any commit setting is stored,
so the message appears until it is acted on and then stops.

Reads the working directory from the hook payload on stdin.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a session from starting.
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

    if commit_settings.any_set(settings_store.load_settings(cwd)):
        return  # Already configured; say nothing.

    # stderr reaches the user's terminal. stdout would reach Claude instead.
    print(commit_settings.SETUP_HELP, file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a session from starting.
        sys.exit(0)
