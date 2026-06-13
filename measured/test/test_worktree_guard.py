"""Tests for hooks/worktree-guard.py — the measured worktree-isolation hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../worktree-guard.py`, so we exercise
that real entrypoint as a subprocess, feeding it the JSON payload shape it sees
on stdin. The contract: exit 0 always; a PreToolUse *deny* on stdout when the
session cwd is inside a linked worktree and the target resolves into the main
checkout; empty stdout (no decision) for everything else.

Each test builds a throwaway git repo and a real linked worktree, so the git
topology the hook inspects is genuine rather than mocked — including the nested
`<main>/…/worktree` layout the harness itself produces under `.claude/worktrees`.
"""

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "worktree-guard.py"


def git(cwd, *args):
    # -c flags keep the test independent of the machine's global git identity.
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=test",
         "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def call(tool_name, cwd, **tool_input):
    return run_hook(json.dumps(
        {"tool_name": tool_name, "tool_input": tool_input, "cwd": str(cwd)}
    ))


class WorktreeGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.main = self.tmp / "main"
        self.main.mkdir()
        git(self.main, "init", "-q")
        (self.main / "file.txt").write_text("main file\n")
        git(self.main, "add", ".")
        git(self.main, "commit", "-q", "-m", "init")
        # Typical layout: the worktree is a sibling of the main checkout.
        self.wt = self.tmp / "wt"
        git(self.main, "worktree", "add", "-q", "-b", "wt", str(self.wt))

    def assert_deny(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")

    def assert_no_decision(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    # --- in a worktree, targeting the main checkout -> deny ---

    def test_deny_read_main(self):
        self.assert_deny(call("Read", self.wt, file_path=str(self.main / "file.txt")))

    def test_deny_edit_main(self):
        self.assert_deny(call("Edit", self.wt, file_path=str(self.main / "file.txt")))

    def test_deny_write_main(self):
        self.assert_deny(call("Write", self.wt, file_path=str(self.main / "new.txt")))

    def test_deny_notebookedit_main(self):
        self.assert_deny(call("NotebookEdit", self.wt, notebook_path=str(self.main / "nb.ipynb")))

    def test_deny_grep_path_main(self):
        self.assert_deny(call("Grep", self.wt, pattern="x", path=str(self.main)))

    def test_deny_glob_path_main(self):
        self.assert_deny(call("Glob", self.wt, pattern="**/*", path=str(self.main)))

    def test_deny_relative_traversal_into_main(self):
        # From the worktree, ../main/file.txt resolves back into the main checkout.
        self.assert_deny(call("Read", self.wt, file_path="../main/file.txt"))

    def test_deny_message_points_into_worktree(self):
        # The reason names the blocked target, the worktree root, and the
        # equivalent in-worktree path the model should use instead.
        target = self.main / "file.txt"
        proc = call("Edit", self.wt, file_path=str(target))
        reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn(str(target.resolve()), reason)
        self.assertIn(str(self.wt.resolve()), reason)
        self.assertIn(str((self.wt / "file.txt").resolve()), reason)

    def test_deny_from_worktree_subdir(self):
        # From a subdir, git reports git-dir/common-dir with mixed abs/relative
        # paths; both must still resolve so the worktree is detected and main blocked.
        sub = self.wt / "deep" / "sub"
        sub.mkdir(parents=True)
        self.assert_deny(call("Edit", sub, file_path=str(self.main / "file.txt")))
        self.assert_no_decision(call("Write", sub, file_path=str(sub / "x.txt")))

    # --- in a worktree, targeting the worktree (or git plumbing) -> no decision ---

    def test_allow_write_inside_worktree(self):
        self.assert_no_decision(call("Write", self.wt, file_path=str(self.wt / "x.txt")))

    def test_allow_read_inside_worktree(self):
        self.assert_no_decision(call("Read", self.wt, file_path=str(self.wt / "file.txt")))

    def test_allow_grep_without_path(self):
        # No path means "search the cwd" — the worktree itself, which is safe.
        self.assert_no_decision(call("Grep", self.wt, pattern="x"))

    def test_allow_glob_without_path(self):
        self.assert_no_decision(call("Glob", self.wt, pattern="**/*"))

    def test_allow_shared_git_dir(self):
        # The worktree's plumbing lives under <main>/.git; keep it reachable.
        self.assert_no_decision(call("Read", self.wt, file_path=str(self.main / ".git" / "config")))

    # --- nested layout: worktree sits *inside* the main working tree ---

    def test_nested_worktree_keeps_itself_writable(self):
        nested = self.main / "sub" / "nested"
        nested.parent.mkdir()
        git(self.main, "worktree", "add", "-q", "-b", "nested", str(nested))
        # Writing inside the nested worktree is allowed even though it is under main.
        self.assert_no_decision(call("Write", nested, file_path=str(nested / "x.txt")))
        # The main checkout outside the nested worktree is still denied.
        self.assert_deny(call("Edit", nested, file_path=str(self.main / "file.txt")))

    # --- not in a worktree, or unevaluable -> no decision ---

    def test_no_decision_in_main_checkout(self):
        self.assert_no_decision(call("Read", self.main, file_path=str(self.main / "file.txt")))

    def test_no_decision_from_main_subdir(self):
        # A subdir of the main checkout, where git reports common-dir as the
        # relative `../.git`. It must resolve equal to git-dir -> not a worktree.
        sub = self.main / "pkg"
        sub.mkdir()
        self.assert_no_decision(call("Write", sub, file_path=str(self.main / "file.txt")))

    def test_no_decision_outside_any_repo(self):
        self.assert_no_decision(call("Read", self.tmp, file_path=str(self.tmp / "x.txt")))

    def test_no_decision_other_tool(self):
        # Bash is out of scope; even an obvious main-checkout reference is ignored.
        self.assert_no_decision(call("Bash", self.wt, command="cat " + str(self.main / "file.txt")))

    def test_no_decision_missing_path(self):
        self.assert_no_decision(run_hook(json.dumps(
            {"tool_name": "Read", "tool_input": {}, "cwd": str(self.wt)}
        )))

    def test_exit_zero_on_junk_stdin(self):
        self.assert_no_decision(run_hook("not even json"))
        self.assert_no_decision(run_hook(""))


if __name__ == "__main__":
    unittest.main()
