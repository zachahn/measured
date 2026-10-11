#!/usr/bin/env python3
"""SessionStart and UserPromptSubmit hook: state a fixed rule to Claude.

One script serves both events. It reads `hook_event_name` from the payload on
stdin and states SESSION_START_RULE on SessionStart and EVERY_TURN_RULE on
UserPromptSubmit. An empty rule prints nothing.

The rules reach Claude only, through `hookSpecificOutput.additionalContext`.

Stdlib-only and tolerant of failure: any unexpected error exits 0 with no
output, so a hook bug can never block a session or a prompt.
"""

import json
import sys

SESSION_START_RULE = """\
Placeholder session-start rule.
"""

EVERY_TURN_RULE = """\
Placeholder every-turn rule.
"""

RULES = {
    "SessionStart": SESSION_START_RULE,
    "UserPromptSubmit": EVERY_TURN_RULE,
}


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    event = payload.get("hook_event_name", "")
    rule = RULES.get(event, "").strip()
    if not rule:
        return  # Unknown event or empty rule; stay quiet.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": rule,
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a session or a prompt.
        sys.exit(0)
