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
<writing-clearly>
- Avoid anthropomorphizing inanimate/software objects.
- Avoid using the present tense verb "names" and "carries" as it's ambiguous and anthropomorphizing.
- Avoid pronouns.
- Connect the true subject directly to its verb.
- Use passive voice.

Example:
- BAD: The merge proposal names the first primary, and the surviving account is the one that carries it.
  - "names" (ambiguous, anthropomorphizing verb)
  - "first primary", "surviving" (three different families of adjectives: "first", "primary", "surviving")
  - "the one" (ambiguous pseudo-pronoun)
  - "carries" (ambiguous, anthropomorphizing verb)
  - "it" (ambiguous pronoun)
- GOOD: The merge proposal will include a proposed primary account, which becomes the surviving account.
- BEST: The user will specify the primary account when creating a merge proposal. Once accepted, all non-primary accounts become hidden in day-to-day user flows.

Example:
- BAD: What decides it: ...
- GOOD: How to decide: ...
- BEST: The key factor is ...
</writing-clearly>
"""

EVERY_TURN_RULE = """\
<writing-clearly-reminder>
- Avoid anthropomorphizing.
- Avoid unnecessary nouns and pronouns.
- Use passive voice.
</writing-clearly-reminder>
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
