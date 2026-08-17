#!/usr/bin/env python3
"""PreToolUse hook: auto-approve Bash calls to measured-behavior-config.

`measured-behavior-config` only reads and writes this plugin's own behavior
settings file; it touches nothing else. Claude runs it often, so prompting for
approval every time is just noise. This hook approves that one case and stays
silent otherwise, letting Claude Code's normal permission flow handle
everything else.

The hook approves a command only when every one of these holds:

1. The raw command contains only characters from `SAFE_CHARS`. That set holds
   no shell metacharacter, so no newline, `;`, `|`, `&`, `$`, backtick,
   redirect, or brace survives it. An allowlist is used rather than a list of
   banned operators because shell grammar is large and a banned-operator list
   keeps losing. A newline is the case that motivates this: bash separates
   commands on a newline exactly as it does on `;`, and `shlex.split` drops a
   newline as ordinary whitespace, so `config --list\\nrm -rf /` would parse to
   a token list whose first token is the target.
2. `argv[0]` is the bare name `measured-behavior-config`, or an absolute path
   that `os.path.realpath` resolves to this plugin's own `bin/` copy. The
   plugin root comes from `__file__`, never from the command, so a lookalike
   binary at `./measured-behavior-config` or `~/evil/measured-behavior-config`
   is refused.
3. The arguments form one of the command's real invocations: no arguments,
   `--list`, `--help`, `-h`, `--get KEY`, `--unset KEY`, or `--set KEY VALUE`,
   each optionally preceded by one scope flag, `--global` or `--repo`. KEY must
   be a known behavior setting. The argument grammar is small and fully known,
   so the hook checks it rather than approving arbitrary argv. `--set` in
   particular writes the file that the reminder hooks inject into Claude's
   context on every later prompt, so its key is worth checking.

We never *deny*; a hook denial would override the user, and the point is only
to remove friction. Stdlib-only and tolerant of failure: any unexpected error
exits 0 with no decision so a hook bug can never block legitimate tool use.
"""

import json
import os
import pathlib
import shlex
import string
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import behavior_settings  # noqa: E402

TARGET = "measured-behavior-config"

# The plugin's own copy of the command. Resolved from this file so a command
# line can never point the check at another directory.
PLUGIN_BIN = pathlib.Path(__file__).resolve().parent.parent / "bin" / TARGET

# Every character a legitimate invocation needs. Holds no shell metacharacter:
# no whitespace other than a plain space, and none of ; | & $ ` ( ) { } < > * ?
# ! ~ # \ or newline. A command carrying anything else is refused unread.
SAFE_CHARS = frozenset(string.ascii_letters + string.digits + " -_./=:,'\"")

# The scope flags the command accepts, one at a time, before any action.
SCOPE_FLAGS = ("--global", "--repo")


def _resolves_to_plugin_bin(program: str) -> bool:
    """Return True if an absolute path names this plugin's own command."""
    if not os.path.isabs(program):
        return False
    try:
        return os.path.realpath(program) == os.path.realpath(PLUGIN_BIN)
    except OSError:
        return False


def _arguments_are_known(args: list[str]) -> bool:
    """Return True if the arguments form one real invocation of the command.

    One leading scope flag is allowed and the rest is checked as usual. The
    scope decides which settings file a write lands in, and both files are the
    command's own, so neither scope widens what the command can touch.
    """
    if not args:
        return True

    if args[0] in SCOPE_FLAGS:
        rest = args[1:]
        if not rest:
            return True  # A bare scope flag prints that scope's settings.
        if rest[0] in SCOPE_FLAGS:
            return False  # The command rejects a second scope flag.
        return _arguments_are_known(rest)

    flag = args[0]
    rest = args[1:]

    if flag in ("--list", "--help", "-h"):
        return not rest
    if flag in ("--get", "--unset"):
        return len(rest) == 1 and rest[0] in behavior_settings.SETTING_KEYS
    if flag == "--set":
        return len(rest) == 2 and rest[0] in behavior_settings.SETTING_KEYS
    return False


def decide(tool_name: str, tool_input: dict) -> bool:
    """Return True if this Bash call should be auto-approved."""
    if tool_name != "Bash":
        return False

    command = tool_input.get("command", "")
    if not command or not set(command) <= SAFE_CHARS:
        return False

    try:
        tokens = shlex.split(command)
    except ValueError:
        return False  # Unbalanced quotes etc. Let the user decide.

    if not tokens:
        return False

    program = tokens[0]
    if program != TARGET and not _resolves_to_plugin_bin(program):
        return False

    return _arguments_are_known(tokens[1:])


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
