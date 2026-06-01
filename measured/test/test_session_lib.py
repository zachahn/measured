"""Tests for lib/session_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import os
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import session_lib as lib  # noqa: E402


class StateRootTest(unittest.TestCase):
    def test_honors_xdg_state_home(self):
        original = os.environ.get("XDG_STATE_HOME")
        try:
            os.environ["XDG_STATE_HOME"] = "/tmp/xdg-state-test"
            self.assertEqual(
                lib.state_root(),
                pathlib.Path("/tmp/xdg-state-test/measured-claude-plugin"),
            )
        finally:
            if original is None:
                del os.environ["XDG_STATE_HOME"]
            else:
                os.environ["XDG_STATE_HOME"] = original

    def test_falls_back_to_home(self):
        original = os.environ.pop("XDG_STATE_HOME", None)
        try:
            self.assertEqual(
                lib.state_root(),
                pathlib.Path.home() / ".local" / "state" / "measured-claude-plugin",
            )
        finally:
            if original is not None:
                os.environ["XDG_STATE_HOME"] = original


class ProcInfoTest(unittest.TestCase):
    def test_returns_real_parent_for_current_pid(self):
        ppid, comm = lib.proc_info(os.getpid())
        self.assertEqual(ppid, os.getppid())
        self.assertTrue(comm, "expected a non-empty comm")


class FindClaudePidTest(unittest.TestCase):
    def test_raises_when_no_claude_ancestor(self):
        # PID 1 (init/launchd) is never named "claude" on a normal system.
        with self.assertRaises(RuntimeError):
            lib.find_claude_pid(1)


class EncodeProjectPathTest(unittest.TestCase):
    def test_replaces_slashes_with_dashes(self):
        self.assertEqual(
            lib.encode_project_path("/Users/zach/Code/Spike/measured"),
            "-Users-zach-Code-Spike-measured",
        )

    def test_relative_path(self):
        self.assertEqual(lib.encode_project_path("a/b/c"), "a-b-c")


class ClaudePwdTest(unittest.TestCase):
    def test_returns_pwd_of_current_process(self):
        # The current process necessarily has a PWD; the helper should find
        # it (or fall back to os.getcwd(), which is the same value).
        self.assertEqual(lib.claude_pwd(os.getpid()), os.getcwd())


if __name__ == "__main__":
    unittest.main()
