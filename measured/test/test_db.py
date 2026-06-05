"""Tests for lib/db.py — the SQLite ID allocator.

Run directly or via `rake test`. Stdlib unittest only.
"""

import pathlib
import sys
import tempfile
import threading
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib"))

import db  # noqa: E402


class DbTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.conn = db.connect(self.repo)
        self.addCleanup(self.conn.close)

    def test_connect_creates_database_file(self):
        self.assertTrue((self.repo / db.DB_FILENAME).exists())

    def test_plan_ids_start_at_one_and_increment(self):
        self.assertEqual(db.allocate_plan(self.conn), 1)
        self.assertEqual(db.allocate_plan(self.conn), 2)

    def test_task_ids_are_global_not_per_plan(self):
        p1 = db.allocate_plan(self.conn)
        p2 = db.allocate_plan(self.conn)
        # Tasks numbered across plans share one sequence.
        self.assertEqual(db.allocate_task(self.conn, p1), 1)
        self.assertEqual(db.allocate_task(self.conn, p2), 2)
        self.assertEqual(db.allocate_task(self.conn, p1), 3)

    def test_task_plan_maps_back(self):
        p1 = db.allocate_plan(self.conn)
        p2 = db.allocate_plan(self.conn)
        t = db.allocate_task(self.conn, p2)
        self.assertEqual(db.task_plan(self.conn, t), p2)
        self.assertNotEqual(db.task_plan(self.conn, t), p1)

    def test_task_plan_unknown_is_none(self):
        self.assertIsNone(db.task_plan(self.conn, 999))

    def test_ids_survive_reconnect(self):
        db.allocate_plan(self.conn)
        self.conn.close()
        conn2 = db.connect(self.repo)
        self.addCleanup(conn2.close)
        # The counter persists; the next plan is 2, never a reused 1.
        self.assertEqual(db.allocate_plan(conn2), 2)

    def test_concurrent_task_allocation_never_collides(self):
        plan_id = db.allocate_plan(self.conn)
        results = []
        lock = threading.Lock()

        def worker():
            # Each thread opens its own connection (SQLite connections are not
            # safe to share across threads) and races to allocate.
            conn = db.connect(self.repo)
            try:
                tid = db.allocate_task(conn, plan_id)
            finally:
                conn.close()
            with lock:
                results.append(tid)

        threads = [threading.Thread(target=worker) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(set(results)), 25, "every task ID must be unique")
        self.assertEqual(sorted(results), list(range(1, 26)))


if __name__ == "__main__":
    unittest.main()
