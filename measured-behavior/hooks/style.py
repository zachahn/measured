#!/usr/bin/env python3
"""UserPromptSubmit hook: remind Claude of the house tone on every prompt.

A SessionStart hook fires once and fades as the session grows. This hook fires
on every prompt the user submits, so the reminder rides in fresh each turn.

UserPromptSubmit hooks add to Claude's context by returning
`hookSpecificOutput.additionalContext`. We emit the one-line reminder there and
ignore stdin, since the prompt payload does not change what we inject.
"""

import json

REMINDER = "Be factual, unemotional, and boring. Write in full sentences."


def main():
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": REMINDER,
        }
    }))


if __name__ == "__main__":
    main()
