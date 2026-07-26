#!/usr/bin/env python3
"""PreToolUse hook: auto-approve Bash calls to measured-behavior-config.

`measured-behavior-config` only reads and writes this plugin's own commit
settings file; it touches nothing else. Claude runs it often, so prompting for
approval every time is just noise. This hook approves that one case and stays
silent otherwise, letting Claude Code's normal permission flow handle
everything else.

Rule: the Bash command, once parsed, must be a single invocation of
`measured-behavior-config` (bare name or a path ending in that name) with
plain arguments — no shell operators. Splitting via shlex and checking
argv[0] (rather than a substring match on the raw command) means a chained or
piped command such as `measured-behavior-config --list; rm -rf /` is refused:
shlex parses that whole string as one token stream, and the semicolon does not
survive as a separate operator, so the token list no longer matches a bare
single-command invocation and the hook stays silent.

We never *deny*; a hook denial would override the user, and the point is only
to remove friction. Stdlib-only and tolerant of failure: any unexpected error
exits 0 with no decision so a hook bug can never block legitimate tool use.
"""

import json
import shlex
import sys

TARGET = "measured-behavior-config"
SHELL_OPERATORS = {"&&", "||", ";", "|", "&", "<", ">", ">>", "<<", "`", "$("}


def decide(tool_name: str, tool_input: dict) -> bool:
    """Return True if this Bash call should be auto-approved."""
    if tool_name != "Bash":
        return False

    command = tool_input.get("command", "")
    if not command or any(op in command for op in SHELL_OPERATORS):
        return False

    try:
        tokens = shlex.split(command)
    except ValueError:
        return False  # Unbalanced quotes etc. — let the user decide.

    if not tokens:
        return False

    program = tokens[0]
    return program == TARGET or program.endswith(f"/{TARGET}")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # No parseable input -> no decision.

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if not decide(tool_name, tool_input):
        return  # Stay silent; Claude Code asks the user as usual.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    "Command is a plain measured-behavior-config invocation."
                ),
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure block a tool call.
        sys.exit(0)
