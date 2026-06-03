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


class AllocateTaskFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_first_call_is_task_001(self):
        path = lib.allocate_task_file(self.dir)
        self.assertEqual(path.name, "TASK-001.md")
        self.assertTrue(path.exists(), "the file must be created, not just named")

    def test_numbers_increment_across_calls(self):
        names = [lib.allocate_task_file(self.dir).name for _ in range(3)]
        self.assertEqual(names, ["TASK-001.md", "TASK-002.md", "TASK-003.md"])

    def test_continues_after_highest_existing_number(self):
        # A gap below the max must not be backfilled — allocation always moves
        # forward from the highest existing number.
        (self.dir / "TASK-005.md").write_text("")
        path = lib.allocate_task_file(self.dir)
        self.assertEqual(path.name, "TASK-006.md")

    def test_ignores_unrelated_filenames(self):
        (self.dir / "TICKET.md").write_text("")
        (self.dir / "TASK-notes.md").write_text("")
        path = lib.allocate_task_file(self.dir)
        self.assertEqual(path.name, "TASK-001.md")

    def test_concurrent_allocation_never_collides(self):
        # Each thread must get a distinct file; O_EXCL guarantees no two
        # callers are handed the same number.
        results = []
        lock = threading.Lock()

        def worker():
            path = lib.allocate_task_file(self.dir)
            with lock:
                results.append(path)

        threads = [threading.Thread(target=worker) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        names = sorted(p.name for p in results)
        self.assertEqual(len(set(names)), 25, "every allocated path must be unique")
        expected = sorted(f"TASK-{i:03d}.md" for i in range(1, 26))
        self.assertEqual(names, expected)


class ListTaskFilesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_empty_directory_returns_empty_list(self):
        self.assertEqual(lib.list_task_files(self.dir), [])

    def test_returns_basenames_in_numeric_order(self):
        # Create out of order to prove sorting is numeric, not lexical.
        for n in (3, 1, 10, 2):
            (self.dir / f"TASK-{n:03d}.md").write_text("")
        self.assertEqual(
            lib.list_task_files(self.dir),
            ["TASK-001.md", "TASK-002.md", "TASK-003.md", "TASK-010.md"],
        )

    def test_ignores_non_task_files(self):
        (self.dir / "TICKET.md").write_text("")
        (self.dir / "TASK-notes.md").write_text("")
        (self.dir / "TASK-001.md").write_text("")
        self.assertEqual(lib.list_task_files(self.dir), ["TASK-001.md"])


class ResolveTaskFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.dir / "TASK-007.md").write_text("")

    def test_resolves_bare_number(self):
        path = lib.resolve_task_file(self.dir, "7")
        self.assertEqual(path, self.dir / "TASK-007.md")

    def test_resolves_stem(self):
        self.assertEqual(
            lib.resolve_task_file(self.dir, "TASK-7"), self.dir / "TASK-007.md"
        )

    def test_resolves_full_filename(self):
        self.assertEqual(
            lib.resolve_task_file(self.dir, "TASK-007.md"), self.dir / "TASK-007.md"
        )

    def test_missing_task_returns_none(self):
        self.assertIsNone(lib.resolve_task_file(self.dir, "8"))

    def test_unparseable_ref_returns_none(self):
        self.assertIsNone(lib.resolve_task_file(self.dir, "banana"))


if __name__ == "__main__":
    unittest.main()
