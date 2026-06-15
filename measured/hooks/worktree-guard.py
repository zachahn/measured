#!/usr/bin/env python3
"""PreToolUse hook: while in a git worktree, deny file access to the main checkout.

The harness can run a session inside a linked git worktree (via EnterWorktree,
`--worktree`, or agent isolation) so its edits stay off the primary working
tree. This hook hardens that boundary: while the session is in a worktree, any
file tool whose target resolves into the *main* worktree's working tree is
denied, so the session can neither read nor overwrite the primary checkout.

Scope: the structured file tools — Read, Edit, Write, NotebookEdit, Grep, Glob
— where the target path is explicit and resolves exactly, plus a narrow Bash
rule. A hook can only scan a Bash command string, not understand it, so the
rule is limited to the obvious shell escape: `cd`/`pushd` into the main tree.
It catches the absolute (`cd /main/checkout/sub`) and relative (`cd ../checkout`)
forms but not every spelling — `git -C`, output redirects, subshells, and
variable expansion slip past — so it raises the bar without sealing Bash.

Detection comes from git, not environment variables:
  - A linked worktree has `--git-dir` (`…/.git/worktrees/<name>`) different from
    `--git-common-dir` (`…/.git`); in the main checkout the two are equal.
  - The main working tree is the parent of that common `.git` directory.

A target is denied when it sits inside the main working tree but outside both
the current worktree's own tree and the shared `.git` directory — so the
worktree's files and its git plumbing stay reachable.

Stdlib-only and tolerant of failure: any unexpected error, a non-repo cwd, or a
main checkout (not a worktree) yields no decision, so the hook can never block
legitimate work or wedge a session. It only ever *denies*; it never approves.
"""

import json
import os
import pathlib
import re
import subprocess
import sys

# Per-tool field naming the path the tool will touch. Grep/Glob may omit it,
# which means "operate on the cwd" — the worktree itself, which is safe — so an
# absent path produces no decision.
TARGET_FIELD = {
    "Read": "file_path",
    "Edit": "file_path",
    "Write": "file_path",
    "NotebookEdit": "notebook_path",
    "Grep": "path",
    "Glob": "path",
}

# Find each `cd`/`pushd` invoked as a command word — at the string start or
# right after a shell separator that begins a new simple command — and capture
# its first argument (a simple or single-/double-quoted token). Conservative by
# design: it skips flags and other spellings rather than risk over-blocking.
_CD_RE = re.compile(
    r"""(?:^|[\n;&|(){}])                   # command boundary
        \s*
        (?P<cmd>cd|pushd)                   # directory-changing builtin
        \s+
        (?P<arg>"[^"]*"|'[^']*'|[^\s;&|()<>]+)  # its first argument
    """,
    re.VERBOSE,
)


def _git(cwd, *args):
    """Run `git -C cwd <args>`; return stripped stdout, or None on any failure."""
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _resolve(base, path_str):
    """Resolve path_str (absolute, or relative to base) to a canonical path.

    Resolving collapses `..` and symlinks so neither can smuggle a target past
    the containment checks. Relative paths resolve against the session cwd.
    """
    if not path_str:
        return None
    try:
        return pathlib.Path(base, path_str).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _is_within(target, root):
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _worktree_trees(cwd):
    """If cwd sits in a linked worktree, return (main_root, toplevel, common_git).

    Returns None when cwd is the main checkout, a bare-main layout, not a repo,
    or git fails — the caller treats None as "no decision".
    """
    info = _git(cwd, "rev-parse", "--git-dir", "--git-common-dir", "--show-toplevel")
    if not info:
        return None
    lines = info.splitlines()
    if len(lines) != 3:
        return None
    git_dir = _resolve(cwd, lines[0])
    common = _resolve(cwd, lines[1])
    toplevel = _resolve(cwd, lines[2])
    if not (git_dir and common and toplevel):
        return None
    if git_dir == common:
        return None  # Main checkout: git-dir and common-dir coincide.
    if common.name != ".git":
        return None  # Bare main or unusual layout — no main working tree to guard.
    return common.parent, toplevel, common


def _blocked_target(target, trees):
    """True when target sits in the main tree but outside the worktree and .git.

    The worktree's own tree and the shared .git can be nested under the main
    root depending on layout; keep both reachable.
    """
    main_root, toplevel, common = trees
    if not _is_within(target, main_root):
        return False
    if _is_within(target, toplevel) or _is_within(target, common):
        return False
    return True


def _decide_bash(command, cwd):
    """Deny a Bash command that `cd`/`pushd`-es into the main checkout.

    Each `cd`/`pushd` target is resolved (absolute, or relative to cwd) and
    checked with the same containment rule the file tools use. Returns the first
    offending command's deny reason, else None.
    """
    if not command:
        return None
    trees = _worktree_trees(cwd)
    if trees is None:
        return None
    for match in _CD_RE.finditer(command):
        arg = match.group("arg").strip("\"'")
        target = _resolve(cwd, arg)
        if target is None or not _blocked_target(target, trees):
            continue
        toplevel = trees[1]
        return (
            f"Bash blocked: `{match.group('cmd')} {arg}` enters the main checkout "
            f"at {target}, but this session is isolated to the git worktree at "
            f"{toplevel}. Work inside the worktree instead."
        )
    return None


def decide(tool_name, tool_input, cwd):
    """Return a deny-reason string for a blocked call, else None (no decision)."""
    if tool_name == "Bash":
        return _decide_bash(tool_input.get("command", ""), cwd)

    field = TARGET_FIELD.get(tool_name)
    if field is None:
        return None
    target = _resolve(cwd, tool_input.get(field, ""))
    if target is None:
        return None  # No explicit path (e.g. Grep/Glob over cwd) — let it through.

    trees = _worktree_trees(cwd)
    if trees is None:
        return None
    if not _blocked_target(target, trees):
        return None
    main_root, toplevel, common = trees
    # Point at the equivalent file inside the worktree: the same repo-relative
    # path, rooted at the worktree instead of the main checkout, so the model
    # can re-target instead of retrying blindly.
    in_worktree = toplevel / target.relative_to(main_root)
    return (
        f"{tool_name} blocked: {target} is in the main checkout, but this session "
        f"is isolated to the git worktree at {toplevel}. Use the copy inside the "
        f"worktree instead: {in_worktree}"
    )


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # No parseable input -> no decision.

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd") or os.getcwd()

    reason = decide(tool_name, tool_input, cwd)
    if reason is None:
        return  # Stay silent; Claude Code's normal flow applies.

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
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
