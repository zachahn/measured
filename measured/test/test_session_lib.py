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


class CachedSessionDirTest(unittest.TestCase):
    """cached_session_dir() should compute session_dir() at most once per key
    and reuse the on-disk result thereafter, while staying correct if the
    cached path is stale."""

    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self._xdg_original = os.environ.get("XDG_STATE_HOME")
        os.environ["XDG_STATE_HOME"] = self._tmp.name

        # A fixed, deterministic key so we don't depend on the real ppid.
        self._key_original = lib._session_cache_key
        lib._session_cache_key = lambda: "test-key"

        # Count how often the expensive path is computed, and where it points.
        self._real_target = lib.state_root() / "projects" / "proj" / "1-2"
        self._real_target.mkdir(parents=True, exist_ok=True)
        self._calls = 0
        self._session_dir_original = lib.session_dir

        def fake_session_dir():
            self._calls += 1
            return self._real_target

        lib.session_dir = fake_session_dir

    def tearDown(self):
        lib.session_dir = self._session_dir_original
        lib._session_cache_key = self._key_original
        if self._xdg_original is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = self._xdg_original
        self._tmp.cleanup()

    def test_miss_computes_then_hit_reuses(self):
        first = lib.cached_session_dir()
        self.assertEqual(first, self._real_target)
        self.assertEqual(self._calls, 1)

        # The cache file should now exist and contain the resolved path.
        cache_file = lib.state_root() / "cache" / "session-dir" / "test-key"
        self.assertTrue(cache_file.is_file())

        # Subsequent calls hit the cache: session_dir() is not called again.
        second = lib.cached_session_dir()
        self.assertEqual(second, self._real_target)
        self.assertEqual(self._calls, 1)

    def test_stale_entry_recomputes(self):
        cache_file = lib.state_root() / "cache" / "session-dir" / "test-key"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("/nonexistent/stale/dir")

        # The cached dir doesn't exist, so it must recompute and overwrite.
        result = lib.cached_session_dir()
        self.assertEqual(result, self._real_target)
        self.assertEqual(self._calls, 1)
        self.assertEqual(cache_file.read_text(), str(self._real_target))


if __name__ == "__main__":
    unittest.main()
