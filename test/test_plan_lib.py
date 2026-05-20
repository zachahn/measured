"""Tests for lib/plan_lib.py.

Run directly or via `rake test`. Stdlib unittest only.
"""

import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import plan_lib as lib  # noqa: E402


class AddItemTest(unittest.TestCase):
    def test_creates_numbered_file_with_header(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            target = lib.add_item(d, "Fix login", "body text")
            self.assertEqual(target.name, "0010.md")
            self.assertEqual(target.read_text(), "# Fix login\n\nbody text\n")

    def test_handles_empty_body(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            target = lib.add_item(d, "Empty", "")
            self.assertEqual(target.read_text(), "# Empty\n")

    def test_increments_sort_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "First", "")
            lib.add_item(d, "Second", "")
            third = lib.add_item(d, "Third", "")
            self.assertEqual(third.name, "0030.md")

    def test_rejects_duplicate_title(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Dup", "")
            with self.assertRaises(ValueError):
                lib.add_item(d, "Dup", "")

    def test_rejects_newline_in_title(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(ValueError):
                lib.add_item(d, "two\nlines", "")
            with self.assertRaises(ValueError):
                lib.add_item(d, "carriage\rreturn", "")

    def test_rejects_empty_or_whitespace_title(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(ValueError):
                lib.add_item(d, "", "")
            with self.assertRaises(ValueError):
                lib.add_item(d, "   ", "")

    def test_preserves_punctuation_in_title(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            for title in ("has: colon", "has/slash", "emoji 🚀 test"):
                path = lib.add_item(d, title, "")
                _, found = lib.find_by_title(d, title)
                self.assertEqual(found, path)


class ListItemsTest(unittest.TestCase):
    def test_returns_items_in_sort_order(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Alpha", "")
            lib.add_item(d, "Beta", "")
            lib.add_item(d, "Gamma", "")
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["Alpha", "Beta", "Gamma"])

    def test_ignores_non_matching_files(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "README.md").write_text("not an item")
            (d / "0010-with-slug.md").write_text("# Old format\n")
            (d / "0010.txt").write_text("wrong extension")
            lib.add_item(d, "Real", "")
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["Real"])

    def test_raises_on_headerless_item_file(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "0010.md").write_text("no header here\n")
            with self.assertRaises(ValueError):
                lib.list_items(d)


class AppendItemTest(unittest.TestCase):
    def test_appends_to_body(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "first\n")
            lib.append_item(d, "Item", "more\n")
            text = (d / "0010.md").read_text()
            self.assertEqual(text, "# Item\n\nfirst\nmore\n")

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(FileNotFoundError):
                lib.append_item(d, "Nope", "x")


class EditItemTest(unittest.TestCase):
    def test_replaces_single_occurrence(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "hello world")
            path, count = lib.edit_item(d, "Item", "world", "there", replace_all=False)
            self.assertIn("hello there", path.read_text())
            self.assertEqual(count, 1)

    def test_rejects_multiple_without_replace_all(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "a a a")
            with self.assertRaises(ValueError):
                lib.edit_item(d, "Item", "a", "b", replace_all=False)

    def test_replace_all(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "a a a")
            path, count = lib.edit_item(d, "Item", "a", "b", replace_all=True)
            self.assertIn("b b b", path.read_text())
            self.assertEqual(count, 3)

    def test_missing_old_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "hello")
            with self.assertRaises(ValueError):
                lib.edit_item(d, "Item", "absent", "x", replace_all=False)

    def test_old_equals_new_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "hello")
            with self.assertRaises(ValueError):
                lib.edit_item(d, "Item", "hello", "hello", replace_all=False)

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(FileNotFoundError):
                lib.edit_item(d, "Nope", "x", "y", replace_all=False)

    def test_can_rename_via_header_edit(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Old name", "body")
            lib.edit_item(d, "Old name", "# Old name", "# New name", replace_all=False)
            _, path = lib.find_by_title(d, "New name")
            self.assertTrue(path.read_text().startswith("# New name\n"))
            with self.assertRaises(FileNotFoundError):
                lib.find_by_title(d, "Old name")

    def test_rejects_rename_to_existing_title(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Alpha", "")
            lib.add_item(d, "Beta", "")
            with self.assertRaises(ValueError):
                lib.edit_item(d, "Alpha", "# Alpha", "# Beta", replace_all=False)
            # Original unchanged.
            _, path = lib.find_by_title(d, "Alpha")
            self.assertTrue(path.read_text().startswith("# Alpha\n"))

    def test_rejects_removing_header(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Item", "body")
            with self.assertRaises(ValueError):
                lib.edit_item(d, "Item", "# Item\n", "", replace_all=False)


class RemoveItemTest(unittest.TestCase):
    def test_deletes_file(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Gone", "")
            lib.remove_item(d, "Gone")
            self.assertEqual(lib.list_items(d), [])

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            with self.assertRaises(FileNotFoundError):
                lib.remove_item(d, "Nope")


class MoveItemTest(unittest.TestCase):
    def test_move_before(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            lib.add_item(d, "B", "")
            lib.add_item(d, "C", "")
            lib.move_item(d, "C", before="B", after=None)
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["A", "C", "B"])

    def test_move_after(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            lib.add_item(d, "B", "")
            lib.add_item(d, "C", "")
            lib.move_item(d, "A", before=None, after="B")
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["B", "A", "C"])

    def test_move_to_front(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            lib.add_item(d, "B", "")
            lib.add_item(d, "C", "")
            lib.move_item(d, "C", before="A", after=None)
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["C", "A", "B"])

    def test_move_to_back(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            lib.add_item(d, "B", "")
            lib.add_item(d, "C", "")
            lib.move_item(d, "A", before=None, after="C")
            titles = [t for _, _, t in lib.list_items(d)]
            self.assertEqual(titles, ["B", "C", "A"])

    def test_requires_exactly_one_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            lib.add_item(d, "B", "")
            with self.assertRaises(ValueError):
                lib.move_item(d, "A", before=None, after=None)
            with self.assertRaises(ValueError):
                lib.move_item(d, "A", before="B", after="B")

    def test_rejects_self_reference(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            with self.assertRaises(ValueError):
                lib.move_item(d, "A", before="A", after=None)

    def test_missing_title_raises(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "")
            with self.assertRaises(FileNotFoundError):
                lib.move_item(d, "Ghost", before="A", after=None)
            with self.assertRaises(FileNotFoundError):
                lib.move_item(d, "A", before="Ghost", after=None)


class ReadAllTest(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(lib.read_all(pathlib.Path(td)), "")

    def test_concatenates_items(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "A", "body a")
            lib.add_item(d, "B", "body b")
            out = lib.read_all(d)
            self.assertIn("# A", out)
            self.assertIn("# B", out)
            self.assertTrue(out.endswith("\n"))


class ReadItemTest(unittest.TestCase):
    def test_reads_one(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            lib.add_item(d, "Only", "hi")
            self.assertEqual(lib.read_item(d, "Only"), "# Only\n\nhi\n")

    def test_missing_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                lib.read_item(pathlib.Path(td), "Ghost")


if __name__ == "__main__":
    unittest.main()
