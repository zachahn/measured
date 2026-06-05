"""Tests for lib/session_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import os
import pathlib
import sys
import tempfile
import threading
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import db  # noqa: E402
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


class RepoDirAtTest(unittest.TestCase):
    def test_uses_path_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "plans"
            self.assertEqual(lib.repo_dir_at(root), root)
            self.assertTrue(root.is_dir(), "expected the dir to be created")

    def test_creates_nested_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "a" / "b" / "c"
            lib.repo_dir_at(root)
            self.assertTrue(root.is_dir())

    def test_expands_user(self):
        home = pathlib.Path.home()
        self.assertEqual(lib.repo_dir_at("~"), home)

    def test_existing_dir_is_fine(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(lib.repo_dir_at(tmp), pathlib.Path(tmp))


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


class ParseRefTest(unittest.TestCase):
    def test_bare_number(self):
        self.assertEqual(lib.parse_ref("7", "TASK"), 7)

    def test_prefixed_stem(self):
        self.assertEqual(lib.parse_ref("TASK-7", "TASK"), 7)
        self.assertEqual(lib.parse_ref("PLAN-3", "PLAN"), 3)

    def test_filename_form(self):
        self.assertEqual(lib.parse_ref("TASK-0007.md", "TASK"), 7)

    def test_case_insensitive_prefix(self):
        self.assertEqual(lib.parse_ref("task-7", "TASK"), 7)

    def test_unparseable_is_none(self):
        self.assertIsNone(lib.parse_ref("banana", "TASK"))
        # A plan ref must not accept the wrong prefix.
        self.assertIsNone(lib.parse_ref("TASK-7", "PLAN"))


class PlanAndTaskTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.conn = db.connect(self.repo)
        self.addCleanup(self.conn.close)

    def test_new_plan_creates_padded_dir(self):
        path = lib.new_plan(self.repo, self.conn)
        self.assertEqual(path.name, "PLAN-0001")
        self.assertTrue(path.is_dir())

    def test_plan_dir_resolves_active(self):
        lib.new_plan(self.repo, self.conn)
        self.assertEqual(
            lib.plan_dir(self.repo, 1), self.repo / "PLAN-0001"
        )

    def test_plan_dir_missing_is_none(self):
        self.assertIsNone(lib.plan_dir(self.repo, 99))

    def test_new_task_uses_global_id_and_creates_file(self):
        p1 = lib.new_plan(self.repo, self.conn)
        p2 = lib.new_plan(self.repo, self.conn)
        # Task IDs are global, so the file numbers continue across plans.
        t1 = lib.new_task(p1, self.conn, 1)
        t2 = lib.new_task(p2, self.conn, 2)
        self.assertEqual(t1.name, "TASK-0001.md")
        self.assertEqual(t2.name, "TASK-0002.md")
        self.assertEqual(t1.parent.name, "PLAN-0001")
        self.assertEqual(t2.parent.name, "PLAN-0002")
        self.assertTrue(t1.exists() and t2.exists())

    def test_list_task_files_numeric_order(self):
        plan = lib.new_plan(self.repo, self.conn)
        for _ in range(3):
            lib.new_task(plan, self.conn, 1)
        # Drop a non-task file to prove it's ignored.
        (plan / "TICKET.md").write_text("")
        self.assertEqual(
            lib.list_task_files(plan),
            ["TASK-0001.md", "TASK-0002.md", "TASK-0003.md"],
        )

    def test_list_empty_plan(self):
        plan = lib.new_plan(self.repo, self.conn)
        self.assertEqual(lib.list_task_files(plan), [])

    def test_resolve_task_file_forms(self):
        plan = lib.new_plan(self.repo, self.conn)
        lib.new_task(plan, self.conn, 1)
        for ref in ("1", "TASK-1", "TASK-0001.md"):
            self.assertEqual(
                lib.resolve_task_file(plan, ref), plan / "TASK-0001.md"
            )
        self.assertIsNone(lib.resolve_task_file(plan, "2"))
        self.assertIsNone(lib.resolve_task_file(plan, "banana"))


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.conn = db.connect(self.repo)
        self.addCleanup(self.conn.close)
        self.plan = lib.new_plan(self.repo, self.conn)
        self.task = lib.new_task(self.plan, self.conn, 1)

    def test_archive_moves_dir_and_contents(self):
        dest = lib.archive_plan(self.repo, 1)
        self.assertEqual(dest, self.repo / "ARCHIVE" / "PLAN-0001")
        self.assertFalse((self.repo / "PLAN-0001").exists())
        self.assertTrue((dest / "TASK-0001.md").exists())

    def test_plan_dir_resolves_archived(self):
        lib.archive_plan(self.repo, 1)
        self.assertEqual(
            lib.plan_dir(self.repo, 1),
            self.repo / "ARCHIVE" / "PLAN-0001",
        )

    def test_round_trip(self):
        lib.archive_plan(self.repo, 1)
        dest = lib.unarchive_plan(self.repo, 1)
        self.assertEqual(dest, self.repo / "PLAN-0001")
        self.assertFalse((self.repo / "ARCHIVE" / "PLAN-0001").exists())

    def test_archive_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            lib.archive_plan(self.repo, 99)

    def test_double_archive_raises(self):
        lib.archive_plan(self.repo, 1)
        # A second active dir reappears, then archiving must refuse to clobber.
        (self.repo / "PLAN-0001").mkdir()
        with self.assertRaises(FileExistsError):
            lib.archive_plan(self.repo, 1)

    def test_unarchive_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            lib.unarchive_plan(self.repo, 1)

    def test_archived_ids_are_not_reused(self):
        # Archiving frees no number: the next plan is 2, never a reused 1.
        lib.archive_plan(self.repo, 1)
        nxt = lib.new_plan(self.repo, self.conn)
        self.assertEqual(nxt.name, "PLAN-0002")


if __name__ == "__main__":
    unittest.main()
