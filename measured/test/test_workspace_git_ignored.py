"""Tests for bin/workspace-git-ignored.

Run directly or via `rake test`. Stdlib unittest only. Each test runs the
script as a module against a throwaway git repo, with global git config
neutralized so the user's own ignore rules don't leak in.
"""

import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "bin" / "workspace-git-ignored"

# The script has no .py extension, so name a SourceFileLoader explicitly.
_loader = importlib.machinery.SourceFileLoader("workspace_git_ignored", str(SCRIPT))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
wgi = importlib.util.module_from_spec(_spec)
_loader.exec_module(wgi)


class WorkspaceGitIgnoredTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

        self._cwd = os.getcwd()
        self.addCleanup(os.chdir, self._cwd)
        os.chdir(self.repo)

        # Neutralize the user's global/system ignore rules so the repo starts
        # with nothing ignored. git reads the default user ignore file at
        # $XDG_CONFIG_HOME/git/ignore (falling back to ~/.config), so redirect
        # HOME and XDG_CONFIG_HOME into the temp dir alongside the config-file
        # overrides.
        self._env = {}
        overrides = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "HOME": str(self.repo),
            "XDG_CONFIG_HOME": str(self.repo / ".empty-xdg"),
        }
        for var, value in overrides.items():
            self._env[var] = os.environ.get(var)
            os.environ[var] = value
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        for var, value in self._env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value

    def run_main(self, *argv: str) -> int:
        return wgi.main(list(argv))

    def test_bare_and_help_match(self):
        from io import StringIO

        bare = StringIO()
        helped = StringIO()
        old = sys.stdout
        try:
            sys.stdout = bare
            self.run_main()
            sys.stdout = helped
            with self.assertRaises(SystemExit):
                self.run_main("--help")
        finally:
            sys.stdout = old
        self.assertEqual(bare.getvalue(), wgi.HELP_TEXT)

    def test_check_not_ignored(self):
        self.assertEqual(self.run_main("--check"), 1)

    def test_fix_gitignore_then_check_passes(self):
        self.assertEqual(self.run_main("--fix-gitignore"), 0)
        self.assertEqual(
            (self.repo / ".gitignore").read_text(),
            ".claude/worktrees/\n",
        )
        self.assertEqual(self.run_main("--check"), 0)

    def test_fix_git_info_exclude_then_check_passes(self):
        self.assertEqual(self.run_main("--fix-git-info-exclude"), 0)
        exclude = (self.repo / ".git" / "info" / "exclude").read_text()
        self.assertIn(".claude/worktrees/", exclude.splitlines())
        self.assertEqual(self.run_main("--check"), 0)

    def test_fix_is_idempotent(self):
        self.run_main("--fix-gitignore")
        self.run_main("--fix-gitignore")
        self.assertEqual(
            (self.repo / ".gitignore").read_text(),
            ".claude/worktrees/\n",
        )

    def test_custom_dir(self):
        self.assertEqual(self.run_main("--check", "build/"), 1)
        self.run_main("--fix-gitignore", "build/")
        self.assertEqual((self.repo / ".gitignore").read_text(), "build/\n")
        self.assertEqual(self.run_main("--check", "build/"), 0)

    def test_outside_git_repo_returns_2(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        os.chdir(outside.name)
        self.assertEqual(self.run_main("--check"), 2)


if __name__ == "__main__":
    unittest.main()
