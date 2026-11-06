#!/usr/bin/env python3
"""SessionStart hook: tell the user the behavior settings exist.

A user who has never stored a behavior setting gets no signal that the settings
exist, so this hook shows a short setup notice when a session starts. It stops
for good once any one of them is stored, in this repo or globally. A global
setting silences the notice in every repo, because a user who set one has found
the feature and needs no further prompting anywhere.

The notice reaches the user, not Claude. It travels in the `systemMessage`
field, which Claude Code shows in the terminal. Two other channels look like
they would work and do not:

- stdout. On SessionStart, stdout becomes Claude's context. Claude needs no
  instruction here, because unset settings mean "behave normally", and
  describing a feature the user has not opted into would spend context to no
  effect.
- stderr. Claude Code reads stderr only when a hook exits non-zero. This hook
  exits 0, so anything written there lands in the debug log and reaches nobody.
  An earlier version of this hook printed the notice to stderr, which is why no
  notice ever appeared.

`systemMessage` rides alongside the JSON payload, so the hook still returns
valid JSON on stdout while showing text to the user.

Reads the working directory from the hook payload on stdin.

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


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()

    if behavior_settings.any_set(settings_store.load_effective_settings(cwd)):
        return  # Already configured here or globally; say nothing.

    # systemMessage reaches the user's terminal. additionalContext would reach
    # Claude instead, and Claude has nothing to do with this message.
    json.dump({"systemMessage": behavior_settings.SETUP_HELP}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a session from starting.
        sys.exit(0)
