"""Tests for lib/ticket_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import os
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import ticket_lib as lib  # noqa: E402


class StepFilesTest(unittest.TestCase):
    def test_sorts_by_numeric_stem_not_lexicographically(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "2.md").write_text("two")
            (d / "10.md").write_text("ten")
            (d / "1.md").write_text("one")
            names = [p.name for p in lib.step_files(d)]
            self.assertEqual(names, ["1.md", "2.md", "10.md"])

    def test_non_numeric_stems_sort_last(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "5.md").write_text("")
            (d / "alpha.md").write_text("")
            names = [p.name for p in lib.step_files(d)]
            self.assertEqual(names, ["5.md", "alpha.md"])

    def test_ignores_non_md_files(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "1.md").write_text("")
            (d / "note.txt").write_text("")
            names = [p.name for p in lib.step_files(d)]
            self.assertEqual(names, ["1.md"])


class ResolveStepTest(unittest.TestCase):
    def test_accepts_filename_with_extension(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "123.md").write_text("body")
            self.assertEqual(lib.resolve_step(d, "123.md").read_text(), "body")

    def test_accepts_filename_without_extension(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "123.md").write_text("body")
            self.assertEqual(lib.resolve_step(d, "123").read_text(), "body")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(ValueError):
                lib.resolve_step(d, "../oops.md")
            with self.assertRaises(ValueError):
                lib.resolve_step(d, "..")
            with self.assertRaises(ValueError):
                lib.resolve_step(d, "")

    def test_rejects_ticket_filename(self):
        # TICKET.md is reserved; reading it as a step would be confusing.
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / lib.TICKET_FILENAME).write_text("body")
            with self.assertRaises(ValueError):
                lib.resolve_step(d, lib.TICKET_FILENAME)
            with self.assertRaises(ValueError):
                lib.resolve_step(d, lib.TICKET_FILENAME.removesuffix(".md"))

    def test_missing_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                lib.resolve_step(pathlib.Path(td), "9999.md")


class WriteStepTest(unittest.TestCase):
    def test_filename_is_ms_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            target = lib.write_step(d, "hello")
            stem = target.stem
            self.assertTrue(stem.isdigit(), f"expected integer stem, got {stem!r}")
            # 13 digits == milliseconds since epoch in the 2001-2286 range.
            self.assertEqual(len(stem), 13)
            self.assertEqual(target.read_text(), "hello")

    def test_back_to_back_writes_do_not_collide(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            names = {lib.write_step(d, str(i)).name for i in range(20)}
            self.assertEqual(len(names), 20)


class WriteTicketTest(unittest.TestCase):
    def test_creates_ticket_md(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            target = lib.write_ticket(d, "# Ticket", force=False)
            self.assertEqual(target.name, lib.TICKET_FILENAME)
            self.assertEqual(target.read_text(), "# Ticket")

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "first", force=False)
            with self.assertRaises(FileExistsError):
                lib.write_ticket(d, "second", force=False)
            self.assertEqual(lib.ticket_path(d).read_text(), "first")

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "first", force=False)
            lib.write_ticket(d, "second", force=True)
            self.assertEqual(lib.ticket_path(d).read_text(), "second")


class EditTicketTest(unittest.TestCase):
    def test_replaces_single_occurrence(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "hello world", force=False)
            target, count = lib.edit_ticket(d, "world", "there", replace_all=False)
            self.assertEqual(target.read_text(), "hello there")
            self.assertEqual(count, 1)

    def test_rejects_multiple_matches_without_replace_all(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "a a a", force=False)
            with self.assertRaises(ValueError):
                lib.edit_ticket(d, "a", "b", replace_all=False)
            self.assertEqual(lib.ticket_path(d).read_text(), "a a a")

    def test_replace_all_replaces_every_occurrence(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "a a a", force=False)
            target, count = lib.edit_ticket(d, "a", "b", replace_all=True)
            self.assertEqual(target.read_text(), "b b b")
            self.assertEqual(count, 3)

    def test_missing_old_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "hello", force=False)
            with self.assertRaises(ValueError):
                lib.edit_ticket(d, "absent", "x", replace_all=False)

    def test_old_equals_new_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.write_ticket(d, "hello", force=False)
            with self.assertRaises(ValueError):
                lib.edit_ticket(d, "hello", "hello", replace_all=False)

    def test_missing_ticket_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                lib.edit_ticket(pathlib.Path(td), "x", "y", replace_all=False)


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


if __name__ == "__main__":
    unittest.main()
