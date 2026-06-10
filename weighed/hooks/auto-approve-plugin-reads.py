#!/usr/bin/env python3
"""PreToolUse hook: auto-approve Read within the weighed plugin's own files.

`/weighed:one-shot` runs the other stages by reading their `SKILL.md` files,
which live in the versioned plugin cache (`~/.claude/plugins/cache/...`) —
outside the project directory, so each read prompts the user. The plugin
reading its own shipped files is safe and the prompt is noise; this hook
approves that one case and stays silent otherwise, letting Claude Code's
normal permission flow handle everything else.

Rule: Read is approved when the resolved target sits under the plugin root
(this script's grandparent directory). Anything else — other tools, paths
outside the plugin, targets that fail to resolve — produces no decision, so
Claude Code falls back to asking the user. We never *deny*; a hook denial
would override the user, and the point is only to remove friction.

Kept stdlib-only and tolerant of failure: any unexpected error exits 0 with
no decision so a hook bug can never block legitimate tool use.
"""

import json
import pathlib
import sys

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _resolve(path_str: str) -> pathlib.Path | None:
    """Resolve a tool's file_path to an absolute, symlink-free path.

    Returns None if it's missing or unresolvable. We resolve so that `..`
    segments and symlinks can't smuggle a path out of the plugin root after
    a naive prefix check.
    """
    if not path_str:
        return None
    try:
        return pathlib.Path(path_str).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def decide(tool_name: str, tool_input: dict) -> bool:
    """Return True if this tool call should be auto-approved."""
    if tool_name != "Read":
        return False

    target = _resolve(tool_input.get("file_path", ""))
    if target is None:
        return False

    try:
        target.relative_to(PLUGIN_ROOT)
        return True
    except ValueError:
        return False


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
                    "Read target is one of the weighed plugin's own files."
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
