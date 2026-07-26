"""Tests for lib/commit_settings.py, lib/settings_store.py, and the hook.

Run directly or via `rake test`. Stdlib unittest only.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "lib"))

import commit_settings  # noqa: E402
import settings_store  # noqa: E402

HOOK = PLUGIN_ROOT / "hooks" / "commit-settings.py"
HELP_HOOK = PLUGIN_ROOT / "hooks" / "commit-settings-help.py"
AGENT_HOOK = PLUGIN_ROOT / "hooks" / "commit-settings-for-agents.py"
CONFIG_BIN = PLUGIN_ROOT / "bin" / "measured-behavior-config"

# The `measured` plugin owns writing the settings file. These tests read its
# session_lib to prove the two path derivations still agree.
MEASURED_LIB = PLUGIN_ROOT.parent / "measured" / "lib"


class StateRootTest(unittest.TestCase):
    def test_honors_xdg_state_home(self):
        with _env(XDG_STATE_HOME="/tmp/xdg-state-test"):
            self.assertEqual(
                settings_store.state_root(),
                pathlib.Path("/tmp/xdg-state-test/measured-claude-plugin"),
            )

    def test_falls_back_to_home(self):
        with _env(XDG_STATE_HOME=None):
            self.assertEqual(
                settings_store.state_root(),
                pathlib.Path.home() / ".local" / "state" / "measured-claude-plugin",
            )


class EncodeProjectPathTest(unittest.TestCase):
    def test_replaces_slashes_with_dashes(self):
        self.assertEqual(
            settings_store.encode_project_path("/Users/zach/Projects/measured"),
            "-Users-zach-Projects-measured",
        )


class MatchesSessionLibTest(unittest.TestCase):
    """The two plugins may not import each other, so guard against drift."""

    def setUp(self):
        if not (MEASURED_LIB / "session_lib.py").exists():
            self.skipTest("measured plugin not present alongside measured-behavior")
        sys.path.insert(0, str(MEASURED_LIB))
        import session_lib  # noqa: PLC0415

        self.session_lib = session_lib

    def test_state_root_matches(self):
        with _env(XDG_STATE_HOME="/tmp/xdg-state-test"):
            self.assertEqual(
                settings_store.state_root(), self.session_lib.state_root()
            )

    def test_repo_dir_matches_for_same_project(self):
        with _env(XDG_STATE_HOME="/tmp/xdg-state-test"):
            for project in ("/Users/zach/Projects/measured", "/tmp/x", "."):
                self.assertEqual(
                    settings_store.repo_dir_for_project(project),
                    self.session_lib.repo_dir_for_project(project),
                    f"path derivation drifted for {project!r}",
                )

    def test_settings_filename_matches(self):
        self.assertEqual(
            settings_store.SETTINGS_FILENAME, self.session_lib.SETTINGS_FILENAME
        )

    def test_reads_what_session_lib_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                project = "/Users/zach/Projects/measured"
                repo = self.session_lib.repo_dir_for_project(project)
                repo.mkdir(parents=True, exist_ok=True)
                self.session_lib.set_setting(repo, "commit-style", "imperative")

                self.assertEqual(
                    settings_store.load_settings(project),
                    {"commit-style": "imperative"},
                )


class LoadSettingsTest(unittest.TestCase):
    def test_returns_empty_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                self.assertEqual(settings_store.load_settings("/nowhere"), {})

    def test_returns_empty_on_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings_text("/some/project", "{not json")
                self.assertEqual(settings_store.load_settings("/some/project"), {})

    def test_returns_empty_when_not_an_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings_text("/some/project", "[1, 2]")
                self.assertEqual(settings_store.load_settings("/some/project"), {})

    def test_reads_a_stored_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"commit-behavior": "on-user-request"})
                self.assertEqual(
                    settings_store.load_settings("/some/project"),
                    {"commit-behavior": "on-user-request"},
                )


class DescribeTest(unittest.TestCase):
    def test_expands_a_known_value(self):
        self.assertEqual(
            commit_settings.describe("commit-behavior", "after-every-turn"),
            "Commit your work at the end of every turn.",
        )

    def test_ignores_case_and_whitespace(self):
        self.assertEqual(
            commit_settings.describe("commit-style", "  Imperative  "),
            commit_settings.describe("commit-style", "imperative"),
        )

    def test_passes_an_unknown_value_through(self):
        self.assertEqual(
            commit_settings.describe("commit-behavior", "commit only on Fridays"),
            "commit only on Fridays",
        )

    def test_passes_through_for_an_unknown_key(self):
        self.assertEqual(commit_settings.describe("nonsense", "value"), "value")

    def test_every_known_value_is_a_nonempty_sentence(self):
        for key, values in commit_settings.KNOWN_VALUES.items():
            self.assertIn(key, commit_settings.COMMIT_KEYS)
            for value, text in values.items():
                self.assertTrue(text.strip(), f"{key}={value} has no text")
                self.assertTrue(
                    text.rstrip().endswith("."), f"{key}={value} is not a sentence"
                )
                self.assertEqual(
                    value, value.strip().lower(), f"{key}={value} is not normalized"
                )


class RenderTest(unittest.TestCase):
    def test_renders_nothing_when_no_settings_are_set(self):
        self.assertEqual(commit_settings.render({}), "")

    def test_ignores_unrelated_settings(self):
        self.assertEqual(
            commit_settings.render({"worktree-setup": "bundle install"}), ""
        )

    def test_skips_blank_and_none_values(self):
        self.assertEqual(
            commit_settings.render({"commit-style": "   ", "commit-body": None}), ""
        )

    def test_renders_one_set_key(self):
        out = commit_settings.render({"commit-style": "imperative"})
        self.assertIn(commit_settings.HEADER, out)
        self.assertIn("- commit-style: Write the subject as an imperative", out)
        self.assertIn(commit_settings.FOOTER, out)
        self.assertNotIn("commit-behavior", out)

    def test_orders_keys_consistently(self):
        out = commit_settings.render(
            {
                "commit-attribution": "false",
                "commit-behavior": "after-every-turn",
                "commit-style": "conventional",
            }
        )
        self.assertLess(out.index("commit-behavior"), out.index("commit-style"))
        self.assertLess(out.index("commit-style"), out.index("commit-attribution"))

    def test_renders_every_commit_instruction(self):
        out = commit_settings.render(
            {key: "true" for key in commit_settings.COMMIT_KEYS}
        )
        for key in commit_settings.REMINDER_KEYS:
            self.assertIn(f"- {key}:", out)


class HookTest(unittest.TestCase):
    def test_prints_nothing_when_no_settings_are_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_run_hook(tmp, {"cwd": "/some/project"}), "")

    def test_prints_nothing_on_unparseable_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_run_hook(tmp, raw="not json"), "")

    def test_emits_additional_context_for_the_payload_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {"commit-behavior": "on-user-request", "commit-style": "imperative"},
                )

            out = _run_hook(tmp, {"cwd": "/some/project"})
            payload = json.loads(out)
            specific = payload["hookSpecificOutput"]

            self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
            context = specific["additionalContext"]
            self.assertIn("Commit only when the user asks", context)
            self.assertIn("imperative sentence", context)

    def test_emits_for_any_prompt(self):
        """The settings reach Claude every turn, not only during a skill."""
        prompts = [
            "what does this repo do",
            "fix the typo in README",
            "/review",
            "",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"commit-location": "current-branch"})

            for prompt in prompts:
                out = _run_hook(tmp, {"cwd": "/some/project", "prompt": prompt})
                context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
                self.assertIn(
                    "branch that is already checked out",
                    context,
                    f"no commit settings injected for prompt {prompt!r}",
                )

    def test_reads_settings_for_the_payload_cwd_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/project/a", {"commit-style": "conventional"})
                _write_settings("/project/b", {"commit-style": "imperative"})

            out = _run_hook(tmp, {"cwd": "/project/b"})
            context = json.loads(out)["hookSpecificOutput"]["additionalContext"]

            self.assertIn("imperative sentence", context)
            self.assertNotIn("Conventional Commits", context)


class AnySetTest(unittest.TestCase):
    def test_false_for_no_settings(self):
        self.assertFalse(commit_settings.any_set({}))

    def test_false_for_unrelated_settings(self):
        self.assertFalse(
            commit_settings.any_set(
                {"worktree-setup": "bundle install", "work-location": "worktree"}
            )
        )

    def test_false_for_blank_values(self):
        self.assertFalse(
            commit_settings.any_set({"commit-style": "  ", "commit-body": None})
        )

    def test_true_for_one_commit_setting(self):
        self.assertTrue(commit_settings.any_set({"commit-signoff": "false"}))


class HelpHookTest(unittest.TestCase):
    def test_prints_setup_help_to_stderr_when_unconfigured(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout, stderr = _run_help_hook(tmp, {"cwd": "/some/project"})

            self.assertIn("no commit settings", stderr)
            self.assertIn("measured-behavior-config --set commit-behavior", stderr)
            self.assertIn("measured-behavior-config --set commit-location", stderr)

    def test_writes_nothing_to_stdout(self):
        """stdout would become Claude's context; the help is for the user."""
        with tempfile.TemporaryDirectory() as tmp:
            stdout, _ = _run_help_hook(tmp, {"cwd": "/some/project"})
            self.assertEqual(stdout, "")

    def test_stays_silent_once_a_setting_is_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"commit-style": "imperative"})

            stdout, stderr = _run_help_hook(tmp, {"cwd": "/some/project"})

            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")

    def test_ignores_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"worktree-setup": "bundle install"})

            _, stderr = _run_help_hook(tmp, {"cwd": "/some/project"})
            self.assertIn("no commit settings", stderr)

    def test_prints_help_on_unparseable_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, stderr = _run_help_hook(tmp, raw="not json")
            self.assertIn("no commit settings", stderr)

    def test_setup_help_names_every_key(self):
        for key in commit_settings.COMMIT_KEYS:
            self.assertIn(key, commit_settings.SETUP_HELP)


class ForwardToAgentsTest(unittest.TestCase):
    def test_off_when_unset(self):
        self.assertFalse(commit_settings.forward_to_agents({}))

    def test_on_for_true_values(self):
        for value in commit_settings.TRUE_VALUES:
            self.assertTrue(
                commit_settings.forward_to_agents(
                    {commit_settings.FORWARD_TO_AGENTS_KEY: value}
                ),
                f"{value!r} should enable forwarding",
            )

    def test_off_for_false_values(self):
        for value in commit_settings.FALSE_VALUES:
            self.assertFalse(
                commit_settings.forward_to_agents(
                    {commit_settings.FORWARD_TO_AGENTS_KEY: value}
                ),
                f"{value!r} should disable forwarding",
            )

    def test_off_for_an_unrecognized_value(self):
        """Rewriting another agent's prompt needs a clear yes."""
        self.assertFalse(
            commit_settings.forward_to_agents(
                {commit_settings.FORWARD_TO_AGENTS_KEY: "maybe"}
            )
        )

    def test_stays_out_of_the_reminder(self):
        out = commit_settings.render(
            {
                commit_settings.FORWARD_TO_AGENTS_KEY: "true",
                "commit-style": "imperative",
            }
        )
        self.assertNotIn(commit_settings.FORWARD_TO_AGENTS_KEY, out)

    def test_alone_does_not_count_as_configured(self):
        """Setting only this key leaves the repo with no commit policy."""
        self.assertFalse(
            commit_settings.any_set({commit_settings.FORWARD_TO_AGENTS_KEY: "true"})
        )


class AgentHookTest(unittest.TestCase):
    PAYLOAD = {
        "cwd": "/some/project",
        "tool_name": "Agent",
        "tool_input": {
            "prompt": "Find all API endpoints",
            "description": "Find endpoints",
            "subagent_type": "Explore",
            "model": "sonnet",
        },
    }

    def _run(self, tmp, payload=None):
        return _run(AGENT_HOOK, tmp, payload or self.PAYLOAD)[0]

    def test_silent_when_forwarding_is_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"commit-style": "imperative"})
            self.assertEqual(self._run(tmp), "")

    def test_silent_when_forwarding_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-style": "imperative",
                        commit_settings.FORWARD_TO_AGENTS_KEY: "false",
                    },
                )
            self.assertEqual(self._run(tmp), "")

    def test_silent_when_no_commit_settings_are_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project", {commit_settings.FORWARD_TO_AGENTS_KEY: "true"}
                )
            self.assertEqual(self._run(tmp), "")

    def test_appends_the_settings_to_the_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-location": "current-branch",
                        commit_settings.FORWARD_TO_AGENTS_KEY: "true",
                    },
                )
            updated = json.loads(self._run(tmp))["hookSpecificOutput"]["updatedInput"]

            self.assertTrue(updated["prompt"].startswith("Find all API endpoints"))
            self.assertIn("branch that is already checked out", updated["prompt"])

    def test_preserves_every_other_field(self):
        """updatedInput replaces the whole object, so nothing may be dropped."""
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-style": "imperative",
                        commit_settings.FORWARD_TO_AGENTS_KEY: "true",
                    },
                )
            updated = json.loads(self._run(tmp))["hookSpecificOutput"]["updatedInput"]

            original = self.PAYLOAD["tool_input"]
            self.assertEqual(set(updated), set(original))
            for field in original:
                if field == "prompt":
                    continue
                self.assertEqual(updated[field], original[field], f"{field} changed")

    def test_grants_no_permission(self):
        """The hook rewrites input; it must not approve the spawn."""
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-style": "imperative",
                        commit_settings.FORWARD_TO_AGENTS_KEY: "true",
                    },
                )
            specific = json.loads(self._run(tmp))["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", specific)

    def test_handles_an_empty_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-style": "imperative",
                        commit_settings.FORWARD_TO_AGENTS_KEY: "true",
                    },
                )
            payload = dict(self.PAYLOAD, tool_input={"prompt": ""})
            updated = json.loads(self._run(tmp, payload))["hookSpecificOutput"][
                "updatedInput"
            ]
            self.assertFalse(updated["prompt"].startswith("\n"))


class ConfigScriptTest(unittest.TestCase):
    def _repo(self, tmp):
        """A working dir for the script, resolved the way its cwd will be.

        On macOS /var and /tmp are symlinks, so the path handed to subprocess
        and the path the script reads back from os.getcwd() differ. Resolving
        here keeps the test writing to the same state dir the script uses.
        """
        repo = os.path.realpath(os.path.join(tmp, "repo"))
        os.makedirs(repo, exist_ok=True)
        return repo

    def _run(self, tmp, *args, cwd):
        env = dict(os.environ, XDG_STATE_HOME=tmp)
        return subprocess.run(
            [sys.executable, str(CONFIG_BIN), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
        )

    def test_sets_and_gets_a_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            self._run(tmp, "--set", "commit-style", "imperative", cwd=cwd)
            got = self._run(tmp, "--get", "commit-style", cwd=cwd)
            self.assertEqual(got.stdout.strip(), "imperative")

    def test_rejects_an_unknown_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            result = self._run(tmp, "--set", "commit-stlye", "imperative", cwd=cwd)
            self.assertEqual(result.returncode, 1)
            self.assertIn("unknown setting", result.stderr)

    def test_preserves_keys_owned_by_the_measured_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(cwd, {"worktree-setup": "bundle install"})

            self._run(tmp, "--set", "commit-style", "imperative", cwd=cwd)

            with _env(XDG_STATE_HOME=tmp):
                stored = settings_store.load_settings(cwd)
            self.assertEqual(stored["worktree-setup"], "bundle install")
            self.assertEqual(stored["commit-style"], "imperative")

    def test_prints_only_commit_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    cwd, {"worktree-setup": "bundle install", "commit-body": "never"}
                )

            printed = json.loads(self._run(tmp, cwd=cwd).stdout)
            self.assertEqual(printed, {"commit-body": "never"})

    def test_unsets_a_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            self._run(tmp, "--set", "commit-body", "never", cwd=cwd)
            self._run(tmp, "--unset", "commit-body", cwd=cwd)
            self.assertEqual(json.loads(self._run(tmp, cwd=cwd).stdout), {})

    def test_stores_free_text_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            rule = "commit only after the last task"
            self._run(tmp, "--set", "commit-behavior", rule, cwd=cwd)
            got = self._run(tmp, "--get", "commit-behavior", cwd=cwd)
            self.assertEqual(got.stdout.strip(), rule)

    def test_list_names_every_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._run(tmp, "--list", cwd=self._repo(tmp)).stdout
            for key in commit_settings.COMMIT_KEYS:
                self.assertIn(key, out)


class ManifestTest(unittest.TestCase):
    """The manifest is what makes the hook fire on every prompt."""

    def setUp(self):
        manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        self.hooks = json.loads(manifest.read_text())["hooks"]

    def _entries(self, event, hook_filename):
        return [
            entry
            for entry in self.hooks.get(event, [])
            for hook in entry.get("hooks", [])
            if hook_filename in hook.get("command", "")
        ]

    def test_registers_the_hook_on_user_prompt_submit(self):
        self.assertEqual(len(self._entries("UserPromptSubmit", "commit-settings.py")), 1)

    def test_hook_has_no_matcher_so_every_prompt_fires_it(self):
        entry = self._entries("UserPromptSubmit", "commit-settings.py")[0]
        self.assertNotIn("matcher", entry)

    def test_registers_the_help_hook_on_session_start(self):
        entries = self._entries("SessionStart", "commit-settings-help.py")
        self.assertEqual(len(entries), 1)

    def test_registers_the_agent_hook_on_the_agent_tool(self):
        entries = self._entries("PreToolUse", "commit-settings-for-agents.py")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["matcher"], "Agent")


class _env:
    """Set env vars for a block, restoring them after. None deletes a var."""

    def __init__(self, **values):
        self.values = values
        self.originals = {}

    def __enter__(self):
        for key, value in self.values.items():
            self.originals[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return self

    def __exit__(self, *exc):
        for key, original in self.originals.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original
        return False


def _write_settings(project, settings):
    _write_settings_text(project, json.dumps(settings))


def _write_settings_text(project, text):
    repo = settings_store.repo_dir_for_project(project)
    repo.mkdir(parents=True, exist_ok=True)
    (repo / settings_store.SETTINGS_FILENAME).write_text(text)


def _run(hook, state_home, payload=None, raw=None):
    """Run a hook as a subprocess and return its (stdout, stderr), stripped."""
    env = dict(os.environ, XDG_STATE_HOME=state_home)
    stdin = raw if raw is not None else json.dumps(payload or {})
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"hook exited {result.returncode}: {result.stderr}"
    return result.stdout.strip(), result.stderr.strip()


def _run_hook(state_home, payload=None, raw=None):
    """Run the per-prompt hook and return its stdout."""
    return _run(HOOK, state_home, payload, raw)[0]


def _run_help_hook(state_home, payload=None, raw=None):
    """Run the startup help hook and return its (stdout, stderr)."""
    return _run(HELP_HOOK, state_home, payload, raw)


if __name__ == "__main__":
    unittest.main()
