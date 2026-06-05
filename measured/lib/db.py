"""SQLite-backed ID allocator for the measured ticketing layout.

One `state.sqlite3` lives in each repo's state dir (next to its PLAN-NNNN
directories). The database owns exactly one thing: the monotonic counters that
hand out plan and task IDs. Content lives in the `.md` files on disk; the
database never mirrors a title, status, or body. A task's on-disk path is
*derived* from its IDs, so the two can never drift.

Task IDs are unique across every plan in the repo (that is what the shared
counter buys over the old per-directory `O_CREAT | O_EXCL` scheme). Allocation
runs inside a `BEGIN IMMEDIATE` transaction so two agents allocating at once
serialize cleanly instead of racing into a half-written row.

Archiving a plan moves its directory under `ARCHIVE/`; it never touches the
database, so an archived plan's number is never freed and never reissued.

Kept stdlib-only so the scripts run from a fresh checkout with no install step.
"""

import pathlib
import sqlite3

DB_FILENAME = "state.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id    INTEGER NOT NULL REFERENCES plans(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(repo_dir: pathlib.Path) -> sqlite3.Connection:
    """Open (creating if needed) the repo's state database, migrated and ready.

    WAL keeps readers from blocking the short allocation writes; a busy timeout
    lets a contending allocator wait for the lock rather than fail outright.
    `repo_dir` must already exist (its caller mkdir's it).
    """
    conn = sqlite3.connect(repo_dir / DB_FILENAME, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def allocate_plan(conn: sqlite3.Connection) -> int:
    """Reserve and return the next plan ID.

    BEGIN IMMEDIATE takes the write lock up front so concurrent callers
    serialize here rather than both reading the same max and colliding.
    """
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute("INSERT INTO plans DEFAULT VALUES")
        return cur.lastrowid


def allocate_task(conn: sqlite3.Connection, plan_id: int) -> int:
    """Reserve and return the next task ID, globally unique within the repo."""
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            "INSERT INTO tasks (plan_id) VALUES (?)", (plan_id,)
        )
        return cur.lastrowid


def task_plan(conn: sqlite3.Connection, task_id: int) -> int | None:
    """Return the plan a task belongs to, or None if no such task.

    This is the one lookup the database answers beyond allocation: it lets
    `--task-get` resolve a global task ID to its file without a plan ref.
    """
    row = conn.execute(
        "SELECT plan_id FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    return row[0] if row else None
