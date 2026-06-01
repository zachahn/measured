#!/usr/bin/env python3
"""PreToolUse hook: auto-approve Read/Edit within the measured state dirs.

Claude routinely reads and edits the plugin's own per-session state (the
TICKET.md / plan files written by `measured-note` and `measured-plan`). Those
live under a predictable on-disk namespace, so prompting for them every time is
just noise. This hook quietly approves the safe cases and stays silent
otherwise, letting Claude Code's normal permission flow handle everything else.

Rules (paths resolved via ../lib/session_lib.py):
  Read  - approved if the target is anywhere under `state_root()`.
  Edit  - approved if the target is under the current `session_dir()`.

`session_dir()` is itself a subtree of `state_root()`, so any editable file is
also readable, which keeps the two rules consistent.

Anything else - other tools, paths outside the state dirs, or a target we can't
resolve - produces no decision, so Claude Code falls back to asking the user.
We never *deny*; a hook denial would override the user, and the whole point
here is only to remove friction, never to add restrictions.

Kept stdlib-only and tolerant of failure: any unexpected error exits 0 with no
decision so a hook bug can never block legitimate tool use.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import session_lib  # noqa: E402

# Both Read and Edit name their target the same way in tool input.
PATH_FIELD = "file_path"


def _resolve(path_str: str) -> pathlib.Path | None:
    """Resolve a tool's file_path to an absolute, symlink-free path.

    Returns None if it's missing or unresolvable. We resolve so that `..`
    segments and symlinks can't smuggle a path out of the state dir after a
    naive prefix check.
    """
    if not path_str:
        return None
    try:
        return pathlib.Path(path_str).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _is_within(target: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def decide(tool_name: str, tool_input: dict) -> bool:
    """Return True if this tool call should be auto-approved."""
    if tool_name not in ("Read", "Edit"):
        return False

    target = _resolve(tool_input.get(PATH_FIELD, ""))
    if target is None:
        return False

    if tool_name == "Read":
        return _is_within(target, session_lib.state_root().resolve())

    # Edit: limited to the current session's own directory.
    return _is_within(target, session_lib.session_dir().resolve())


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
                    f"{tool_name} target is within the measured plugin's state directory."
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
