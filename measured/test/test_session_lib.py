"""Tests for lib/session_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import datetime
import os
import pathlib
import sys
import tempfile
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


class RepoDirForProjectTest(unittest.TestCase):
    def test_encodes_absolute_path_under_projects(self):
        original = os.environ.get("XDG_STATE_HOME")
        try:
            os.environ["XDG_STATE_HOME"] = "/tmp/xdg-rdp-test"
            self.assertEqual(
                lib.repo_dir_for_project("/Users/zach/Projects/measured"),
                pathlib.Path(
                    "/tmp/xdg-rdp-test/measured-claude-plugin/projects"
                    "/-Users-zach-Projects-measured"
                ),
            )
        finally:
            if original is None:
                del os.environ["XDG_STATE_HOME"]
            else:
                os.environ["XDG_STATE_HOME"] = original

    def test_resolves_relative_path_to_cwd(self):
        # "." encodes the current working directory's absolute path.
        expected = lib.repo_dir_for_project(os.getcwd())
        self.assertEqual(lib.repo_dir_for_project("."), expected)

    def test_does_not_create_the_dir(self):
        path = lib.repo_dir_for_project("/no/such/place/xyz")
        self.assertFalse(path.exists())


class ClaudePwdTest(unittest.TestCase):
    def test_returns_pwd_of_current_process(self):
        # The current process necessarily has a PWD; the helper should find
        # it (or fall back to os.getcwd(), which is the same value).
        self.assertEqual(lib.claude_pwd(os.getpid()), os.getcwd())


class SanitizeSlugTest(unittest.TestCase):
    def test_lowercases_and_kebabs(self):
        self.assertEqual(
            lib.sanitize_slug("Simplify measured-notes"),
            "simplify-measured-notes",
        )

    def test_collapses_runs_of_non_alphanumeric(self):
        self.assertEqual(lib.sanitize_slug("a -- b __ c"), "a-b-c")

    def test_trims_leading_and_trailing_hyphens(self):
        self.assertEqual(lib.sanitize_slug("  hello!  "), "hello")

    def test_empty_when_nothing_alphanumeric(self):
        self.assertEqual(lib.sanitize_slug("!!!"), "")
        self.assertEqual(lib.sanitize_slug("   "), "")


class NewPlanDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_creates_dated_dir(self):
        path = lib.new_plan_dir(self.repo, "Simplify measured-notes")
        today = datetime.date.today().isoformat()
        self.assertEqual(path.name, f"{today}-simplify-measured-notes")
        self.assertEqual(path.parent, self.repo)
        self.assertTrue(path.is_dir())

    def test_empty_slug_raises_and_creates_nothing(self):
        with self.assertRaises(ValueError):
            lib.new_plan_dir(self.repo, "!!!")
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_collision_raises_and_leaves_existing(self):
        first = lib.new_plan_dir(self.repo, "same slug")
        (first / "TICKET.md").write_text("keep me")
        with self.assertRaises(FileExistsError):
            lib.new_plan_dir(self.repo, "same slug")
        # The existing dir and its contents are untouched.
        self.assertEqual((first / "TICKET.md").read_text(), "keep me")
        self.assertEqual(len(list(self.repo.iterdir())), 1)


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_load_returns_empty_when_absent(self):
        self.assertEqual(lib.load_settings(self.repo), {})

    def test_set_then_get_roundtrips(self):
        lib.set_setting(self.repo, "worktree-setup", "npm install")
        self.assertEqual(lib.get_setting(self.repo, "worktree-setup"), "npm install")

    def test_set_writes_pretty_json_with_trailing_newline(self):
        lib.set_setting(self.repo, "worktree-setup", "npm install")
        text = lib.settings_path(self.repo).read_text()
        self.assertEqual(text, '{\n  "worktree-setup": "npm install"\n}\n')

    def test_set_updates_existing_key(self):
        lib.set_setting(self.repo, "worktree-setup", "npm install")
        lib.set_setting(self.repo, "worktree-setup", "make")
        self.assertEqual(lib.load_settings(self.repo), {"worktree-setup": "make"})

    def test_set_none_deletes_key(self):
        lib.set_setting(self.repo, "worktree-setup", "npm install")
        lib.set_setting(self.repo, "other", "keep")
        lib.set_setting(self.repo, "worktree-setup", None)
        self.assertEqual(lib.load_settings(self.repo), {"other": "keep"})

    def test_get_returns_none_for_unset_key(self):
        self.assertIsNone(lib.get_setting(self.repo, "missing"))

    def test_load_rejects_non_object_json(self):
        lib.settings_path(self.repo).write_text("[1, 2, 3]")
        with self.assertRaises(ValueError):
            lib.load_settings(self.repo)


if __name__ == "__main__":
    unittest.main()
