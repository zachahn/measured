"""Tests for lib/note_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import note_lib as lib  # noqa: E402


class NotePathTest(unittest.TestCase):
    def test_ticket_filename(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            self.assertEqual(lib.note_path(d, lib.NOTE_TICKET).name, "TICKET.md")


class NoteDirTest(unittest.TestCase):
    def test_creates_note_subdirectory(self):
        with tempfile.TemporaryDirectory() as td:
            session = pathlib.Path(td)
            target = lib.note_dir(session)
            self.assertEqual(target, session / "note")
            self.assertTrue(target.is_dir())


class ReadNoteTest(unittest.TestCase):
    def test_reads_existing_note(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "TICKET.md").write_text("body")
            self.assertEqual(lib.read_note(d, lib.NOTE_TICKET), "body")

    def test_missing_note_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                lib.read_note(pathlib.Path(td), lib.NOTE_TICKET)


class AppendNoteTest(unittest.TestCase):
    def test_creates_note_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            target = lib.append_note(d, lib.NOTE_TICKET, "first")
            self.assertEqual(target.name, "TICKET.md")
            self.assertEqual(target.read_text(), "first")

    def test_appends_to_existing_note(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "a")
            lib.append_note(d, lib.NOTE_TICKET, "b")
            self.assertEqual(lib.note_path(d, lib.NOTE_TICKET).read_text(), "ab")


class EditNoteTest(unittest.TestCase):
    def test_replaces_single_occurrence(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "hello world")
            target, count = lib.edit_note(d, lib.NOTE_TICKET, "world", "there", replace_all=False)
            self.assertEqual(target.read_text(), "hello there")
            self.assertEqual(count, 1)

    def test_rejects_multiple_matches_without_replace_all(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "a a a")
            with self.assertRaises(ValueError):
                lib.edit_note(d, lib.NOTE_TICKET, "a", "b", replace_all=False)
            self.assertEqual(lib.note_path(d, lib.NOTE_TICKET).read_text(), "a a a")

    def test_replace_all_replaces_every_occurrence(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "a a a")
            target, count = lib.edit_note(d, lib.NOTE_TICKET, "a", "b", replace_all=True)
            self.assertEqual(target.read_text(), "b b b")
            self.assertEqual(count, 3)

    def test_missing_old_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "hello")
            with self.assertRaises(ValueError):
                lib.edit_note(d, lib.NOTE_TICKET, "absent", "x", replace_all=False)

    def test_old_equals_new_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.append_note(d, lib.NOTE_TICKET, "hello")
            with self.assertRaises(ValueError):
                lib.edit_note(d, lib.NOTE_TICKET, "hello", "hello", replace_all=False)

    def test_missing_note_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                lib.edit_note(pathlib.Path(td), lib.NOTE_TICKET, "x", "y", replace_all=False)


if __name__ == "__main__":
    unittest.main()
