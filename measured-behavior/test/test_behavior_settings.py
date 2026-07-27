"""Tests for lib/behavior_settings.py, lib/settings_store.py, and the hooks.

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

import behavior_settings  # noqa: E402
import settings_store  # noqa: E402

HOOK = PLUGIN_ROOT / "hooks" / "reminders-every-turn.py"
START_HOOK = PLUGIN_ROOT / "hooks" / "reminders-session-start.py"
HELP_HOOK = PLUGIN_ROOT / "hooks" / "setup-notice.py"
SUBAGENT_HOOK = PLUGIN_ROOT / "hooks" / "commit-settings-for-subagents.py"
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
            behavior_settings.describe("commit-behavior", "after-every-turn"),
            "Commit your work at the end of every turn.",
        )

    def test_ignores_case_and_whitespace(self):
        self.assertEqual(
            behavior_settings.describe("commit-style", "  Imperative  "),
            behavior_settings.describe("commit-style", "imperative"),
        )

    def test_passes_an_unknown_value_through(self):
        self.assertEqual(
            behavior_settings.describe("commit-behavior", "commit only on Fridays"),
            "commit only on Fridays",
        )

    def test_passes_through_for_an_unknown_key(self):
        self.assertEqual(behavior_settings.describe("nonsense", "value"), "value")

    def test_every_known_value_is_a_nonempty_sentence(self):
        for key, values in behavior_settings.KNOWN_VALUES.items():
            self.assertIn(key, behavior_settings.SETTING_KEYS)
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
        self.assertEqual(behavior_settings.render({}), "")

    def test_ignores_unrelated_settings(self):
        self.assertEqual(
            behavior_settings.render({"worktree-setup": "bundle install"}), ""
        )

    def test_skips_blank_and_none_values(self):
        self.assertEqual(
            behavior_settings.render({"commit-style": "   ", "commit-body": None}), ""
        )

    def test_renders_one_set_key(self):
        out = behavior_settings.render({"commit-style": "imperative"})
        self.assertIn(behavior_settings.HEADER, out)
        self.assertIn("- commit-style: Write the subject as an imperative", out)
        self.assertIn(behavior_settings.FOOTER, out)
        self.assertNotIn("commit-behavior", out)

    def test_orders_keys_consistently(self):
        out = behavior_settings.render(
            {
                "commit-claude-attribution": "false",
                "commit-behavior": "after-every-turn",
                "commit-style": "conventional",
            }
        )
        self.assertLess(out.index("commit-behavior"), out.index("commit-style"))
        self.assertLess(out.index("commit-style"), out.index("commit-claude-attribution"))

    def test_renders_every_commit_instruction(self):
        out = behavior_settings.render(
            {key: "true" for key in behavior_settings.COMMIT_KEYS}
        )
        for key in behavior_settings.REMINDER_KEYS:
            self.assertIn(f"- {key}:", out)


class HookTest(unittest.TestCase):
    """Payload handling in the every-turn hook.

    These cases are about reading the payload, not about timing, so they store
    `every-turn` to put the commit settings on the prompt where they can be
    asserted against. `EveryTurnHookTest` covers the timing itself.
    """

    EVERY_TURN = {behavior_settings.COMMIT_TIMING_KEY: "every-turn"}

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
                    {
                        "commit-behavior": "on-user-request",
                        "commit-style": "imperative",
                        **self.EVERY_TURN,
                    },
                )

            out = _run_hook(tmp, {"cwd": "/some/project"})
            payload = json.loads(out)
            specific = payload["hookSpecificOutput"]

            self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
            context = specific["additionalContext"]
            self.assertIn("Commit only when the user asks", context)
            self.assertIn("imperative sentence", context)

    def test_emits_for_any_prompt(self):
        """The settings reach Claude on any prompt, not only during a skill."""
        prompts = [
            "what does this repo do",
            "fix the typo in README",
            "/review",
            "",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {"commit-location": "current-branch", **self.EVERY_TURN},
                )

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
                _write_settings(
                    "/project/a", {"commit-style": "conventional", **self.EVERY_TURN}
                )
                _write_settings(
                    "/project/b", {"commit-style": "imperative", **self.EVERY_TURN}
                )

            out = _run_hook(tmp, {"cwd": "/project/b"})
            context = json.loads(out)["hookSpecificOutput"]["additionalContext"]

            self.assertIn("imperative sentence", context)
            self.assertNotIn("Conventional Commits", context)


class AnySetTest(unittest.TestCase):
    """`any_set` drives the startup notice; `any_commit_set` drives nothing else."""

    def test_false_for_no_settings(self):
        self.assertFalse(behavior_settings.any_set({}))

    def test_false_for_unrelated_settings(self):
        self.assertFalse(
            behavior_settings.any_set(
                {"worktree-setup": "bundle install", "work-location": "worktree"}
            )
        )

    def test_false_for_blank_values(self):
        self.assertFalse(
            behavior_settings.any_set({"commit-style": "  ", "commit-body": None})
        )

    def test_true_for_one_commit_setting(self):
        self.assertTrue(behavior_settings.any_set({"commit-body": "never"}))

    def test_true_for_the_comment_setting_alone(self):
        """Configuring only comments still means the user found the feature."""
        self.assertTrue(
            behavior_settings.any_set({behavior_settings.COMMENT_KEY: "never"})
        )

    def test_true_for_the_timing_key_alone(self):
        self.assertTrue(
            behavior_settings.any_set(
                {behavior_settings.COMMIT_TIMING_KEY: "session-start"}
            )
        )

    def test_commit_set_ignores_the_comment_setting(self):
        """A comment policy says nothing about how to commit."""
        self.assertFalse(
            behavior_settings.any_commit_set({behavior_settings.COMMENT_KEY: "never"})
        )
        self.assertTrue(behavior_settings.any_commit_set({"commit-body": "never"}))


class SetupNoticeTest(unittest.TestCase):
    """The notice must reach the user's terminal, not the debug log.

    An earlier version printed to stderr and exited 0. Claude Code reads a
    hook's stderr only when it exits non-zero, so that notice reached nobody.
    It travels in `systemMessage` now, which the terminal shows.
    """

    def test_shows_the_notice_as_a_system_message_when_unconfigured(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout, _ = _run_help_hook(tmp, {"cwd": "/some/project"})

            message = json.loads(stdout)["systemMessage"]
            self.assertIn("no behavior settings", message)
            self.assertIn("/measured-behavior:config", message)

    def test_writes_nothing_to_stderr(self):
        """stderr goes to the debug log on exit 0, so nothing may rely on it."""
        with tempfile.TemporaryDirectory() as tmp:
            _, stderr = _run_help_hook(tmp, {"cwd": "/some/project"})
            self.assertEqual(stderr, "")

    def test_adds_no_context_for_claude(self):
        """Claude needs no instruction about a feature the user has not chosen."""
        with tempfile.TemporaryDirectory() as tmp:
            stdout, _ = _run_help_hook(tmp, {"cwd": "/some/project"})
            payload = json.loads(stdout)

            self.assertNotIn("additionalContext", payload)
            self.assertNotIn("hookSpecificOutput", payload)

    def test_stays_silent_once_a_setting_is_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"commit-style": "imperative"})

            stdout, stderr = _run_help_hook(tmp, {"cwd": "/some/project"})

            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")

    def test_stays_silent_once_only_comments_are_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project", {behavior_settings.COMMENT_KEY: "never"}
                )

            stdout, _ = _run_help_hook(tmp, {"cwd": "/some/project"})
            self.assertEqual(stdout, "")

    def test_ignores_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings("/some/project", {"worktree-setup": "bundle install"})

            stdout, _ = _run_help_hook(tmp, {"cwd": "/some/project"})
            self.assertIn("no behavior settings", json.loads(stdout)["systemMessage"])

    def test_shows_the_notice_on_unparseable_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout, _ = _run_help_hook(tmp, raw="not json")
            self.assertIn("no behavior settings", json.loads(stdout)["systemMessage"])

    def test_setup_help_names_every_key(self):
        for key in behavior_settings.SETTING_KEYS:
            self.assertIn(key, behavior_settings.SETUP_HELP)


class ForwardToAgentsTest(unittest.TestCase):
    def test_off_when_unset(self):
        self.assertFalse(behavior_settings.forward_to_subagents({}))

    def test_on_for_true_values(self):
        for value in behavior_settings.TRUE_VALUES:
            self.assertTrue(
                behavior_settings.forward_to_subagents(
                    {behavior_settings.FORWARD_TO_SUBAGENTS_KEY: value}
                ),
                f"{value!r} should enable forwarding",
            )

    def test_off_for_false_values(self):
        for value in behavior_settings.FALSE_VALUES:
            self.assertFalse(
                behavior_settings.forward_to_subagents(
                    {behavior_settings.FORWARD_TO_SUBAGENTS_KEY: value}
                ),
                f"{value!r} should disable forwarding",
            )

    def test_off_for_an_unrecognized_value(self):
        """Rewriting another agent's prompt needs a clear yes."""
        self.assertFalse(
            behavior_settings.forward_to_subagents(
                {behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "maybe"}
            )
        )

    def test_stays_out_of_the_reminder(self):
        out = behavior_settings.render(
            {
                behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true",
                "commit-style": "imperative",
            }
        )
        self.assertNotIn(behavior_settings.FORWARD_TO_SUBAGENTS_KEY, out)

    def test_alone_is_no_commit_policy(self):
        """Setting only this key leaves the repo with nothing to say about commits."""
        self.assertFalse(
            behavior_settings.any_commit_set(
                {behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true"}
            )
        )

    def test_alone_still_silences_the_setup_notice(self):
        """The user who set it has found the feature; the notice has done its job."""
        self.assertTrue(
            behavior_settings.any_set({behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true"})
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
        return _run(SUBAGENT_HOOK, tmp, payload or self.PAYLOAD)[0]

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
                        behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "false",
                    },
                )
            self.assertEqual(self._run(tmp), "")

    def test_silent_when_no_commit_settings_are_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project", {behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true"}
                )
            self.assertEqual(self._run(tmp), "")

    def test_appends_the_settings_to_the_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _env(XDG_STATE_HOME=tmp):
                _write_settings(
                    "/some/project",
                    {
                        "commit-location": "current-branch",
                        behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true",
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
                        behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true",
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
                        behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true",
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
                        behavior_settings.FORWARD_TO_SUBAGENTS_KEY: "true",
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
            for key in behavior_settings.SETTING_KEYS:
                self.assertIn(key, out)

    def test_writes_and_reads_the_new_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            for key, value in (
                (behavior_settings.COMMENT_KEY, "exceptional-only"),
                (behavior_settings.COMMIT_TIMING_KEY, "session-start"),
            ):
                self._run(tmp, "--set", key, value, cwd=cwd)
                got = self._run(tmp, "--get", key, cwd=cwd)
                self.assertEqual(got.stdout.strip(), value)

    def test_unsetting_the_comment_key_silences_the_reminder(self):
        """Unset must return the repo to Claude commenting as it normally would."""
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._repo(tmp)
            self._run(tmp, "--set", behavior_settings.COMMENT_KEY, "never", cwd=cwd)
            self._run(tmp, "--unset", behavior_settings.COMMENT_KEY, cwd=cwd)

            with _env(XDG_STATE_HOME=tmp):
                stored = settings_store.load_settings(cwd)
            self.assertEqual(behavior_settings.render_comment(stored), "")


class CommitTimingTest(unittest.TestCase):
    def test_defaults_to_session_start(self):
        self.assertEqual(
            behavior_settings.commit_timing({}), behavior_settings.SESSION_START
        )

    def test_reads_every_turn(self):
        self.assertEqual(
            behavior_settings.commit_timing(
                {behavior_settings.COMMIT_TIMING_KEY: "every-turn"}
            ),
            behavior_settings.EVERY_TURN,
        )

    def test_reads_session_start(self):
        self.assertEqual(
            behavior_settings.commit_timing(
                {behavior_settings.COMMIT_TIMING_KEY: "session-start"}
            ),
            behavior_settings.SESSION_START,
        )

    def test_ignores_case_and_whitespace(self):
        self.assertEqual(
            behavior_settings.commit_timing(
                {behavior_settings.COMMIT_TIMING_KEY: "  Every-Turn  "}
            ),
            behavior_settings.EVERY_TURN,
        )

    def test_falls_back_to_the_default_for_an_unknown_value(self):
        """The key takes two values, so free text describes neither."""
        self.assertEqual(
            behavior_settings.commit_timing(
                {behavior_settings.COMMIT_TIMING_KEY: "sometimes"}
            ),
            behavior_settings.SESSION_START,
        )

    def test_stays_out_of_the_commit_reminder(self):
        out = behavior_settings.render(
            {
                behavior_settings.COMMIT_TIMING_KEY: "session-start",
                "commit-style": "imperative",
            }
        )
        self.assertNotIn(behavior_settings.COMMIT_TIMING_KEY, out)


class RenderCommentTest(unittest.TestCase):
    def test_renders_nothing_when_unset(self):
        """Unset means Claude never learns the setting exists."""
        self.assertEqual(behavior_settings.render_comment({}), "")

    def test_renders_nothing_for_a_blank_value(self):
        self.assertEqual(
            behavior_settings.render_comment({behavior_settings.COMMENT_KEY: "  "}), ""
        )

    def test_renders_never(self):
        out = behavior_settings.render_comment({behavior_settings.COMMENT_KEY: "never"})
        self.assertIn(behavior_settings.COMMENT_HEADER, out)
        self.assertIn("Write no comments", out)
        self.assertIn(behavior_settings.FOOTER, out)

    def test_renders_exceptional_only(self):
        out = behavior_settings.render_comment(
            {behavior_settings.COMMENT_KEY: "exceptional-only"}
        )
        self.assertIn("Comment on why, never on what", out)

    def test_passes_free_text_through(self):
        out = behavior_settings.render_comment(
            {behavior_settings.COMMENT_KEY: "comment every public method"}
        )
        self.assertIn("comment every public method", out)

    def test_stays_out_of_the_commit_reminder(self):
        out = behavior_settings.render(
            {behavior_settings.COMMENT_KEY: "never", "commit-style": "imperative"}
        )
        self.assertNotIn(behavior_settings.COMMENT_KEY, out)


class EveryTurnHookTest(unittest.TestCase):
    """Which reminders ride on a user prompt."""

    def _context(self, tmp, settings):
        with _env(XDG_STATE_HOME=tmp):
            _write_settings("/some/project", settings)
        out = _run_hook(tmp, {"cwd": "/some/project"})
        if not out:
            return ""
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]

    def test_omits_the_commit_settings_by_default(self):
        """The session-start hook owns them unless the repo asks otherwise."""
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(tmp, {"commit-location": "current-branch"})
            self.assertEqual(context, "")

    def test_states_the_commit_settings_for_an_every_turn_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(
                tmp,
                {
                    "commit-location": "current-branch",
                    behavior_settings.COMMIT_TIMING_KEY: "every-turn",
                },
            )
            self.assertIn("branch that is already checked out", context)

    def test_states_the_comment_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(tmp, {behavior_settings.COMMENT_KEY: "never"})
            self.assertIn("Write no comments", context)

    def test_states_the_comment_setting_under_the_default_timing(self):
        """The timing key governs the commit settings only."""
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(
                tmp,
                {
                    behavior_settings.COMMENT_KEY: "never",
                    "commit-style": "imperative",
                },
            )
            self.assertIn("Write no comments", context)
            self.assertNotIn("imperative sentence", context)

    def test_states_both_reminders_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(
                tmp,
                {
                    "commit-style": "imperative",
                    behavior_settings.COMMENT_KEY: "exceptional-only",
                    behavior_settings.COMMIT_TIMING_KEY: "every-turn",
                },
            )
            self.assertIn("imperative sentence", context)
            self.assertIn("Comment on why", context)
            self.assertLess(
                context.index(behavior_settings.HEADER),
                context.index(behavior_settings.COMMENT_HEADER),
            )

    def test_silent_when_only_the_timing_key_is_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = self._context(
                tmp, {behavior_settings.COMMIT_TIMING_KEY: "every-turn"}
            )
            self.assertEqual(context, "")


class SessionStartHookTest(unittest.TestCase):
    """The commit reminder for a repo that asked for it once a session."""

    def _start(self, tmp, settings):
        with _env(XDG_STATE_HOME=tmp):
            _write_settings("/some/project", settings)
        return _run(START_HOOK, tmp, {"cwd": "/some/project"})[0]

    def test_states_the_commit_settings_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self._start(tmp, {"commit-style": "imperative"})
            specific = json.loads(out)["hookSpecificOutput"]

            self.assertEqual(specific["hookEventName"], "SessionStart")
            self.assertIn("imperative sentence", specific["additionalContext"])

    def test_silent_for_an_every_turn_repo(self):
        """Exactly one hook states the settings, so they never arrive twice."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self._start(
                    tmp,
                    {
                        "commit-style": "imperative",
                        behavior_settings.COMMIT_TIMING_KEY: "every-turn",
                    },
                ),
                "",
            )

    def test_silent_when_no_commit_setting_is_stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self._start(tmp, {behavior_settings.COMMENT_KEY: "never"}), ""
            )

    def test_omits_the_comment_setting(self):
        """The every-turn hook owns the comment reminder."""
        with tempfile.TemporaryDirectory() as tmp:
            out = self._start(
                tmp,
                {
                    "commit-style": "imperative",
                    behavior_settings.COMMENT_KEY: "never",
                },
            )
            context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("Write no comments", context)

    def test_prints_nothing_on_unparseable_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_run(START_HOOK, tmp, raw="not json")[0], "")


class ManifestTest(unittest.TestCase):
    """The manifest is what makes the hooks fire."""

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
        entries = self._entries("UserPromptSubmit", "reminders-every-turn.py")
        self.assertEqual(len(entries), 1)

    def test_hook_has_no_matcher_so_every_prompt_fires_it(self):
        entry = self._entries("UserPromptSubmit", "reminders-every-turn.py")[0]
        self.assertNotIn("matcher", entry)

    def test_registers_the_session_start_reminder(self):
        entries = self._entries("SessionStart", "reminders-session-start.py")
        self.assertEqual(len(entries), 1)

    def test_session_start_reminder_fires_on_every_source(self):
        """Each source drops the context holding the settings, so all must fire.

        `compact`, `clear`, and `fork` matter most. A session that keeps running
        past one of them without the settings commits the wrong way afterward.
        """
        entry = self._entries("SessionStart", "reminders-session-start.py")[0]
        sources = set(entry["matcher"].split("|"))
        self.assertEqual(
            sources, {"startup", "resume", "clear", "compact", "fork"}
        )

    def test_registers_the_setup_notice_on_session_start(self):
        entries = self._entries("SessionStart", "setup-notice.py")
        self.assertEqual(len(entries), 1)

    def test_every_registered_hook_file_exists(self):
        """A renamed hook that the manifest still points at would fail silently."""
        for event, entries in self.hooks.items():
            for entry in entries:
                for hook in entry.get("hooks", []):
                    name = hook["command"].rsplit("/", 1)[-1]
                    self.assertTrue(
                        (PLUGIN_ROOT / "hooks" / name).is_file(),
                        f"{event} points at a missing hook: {name}",
                    )

    def test_registers_the_agent_hook_on_the_agent_tool(self):
        entries = self._entries("PreToolUse", "commit-settings-for-subagents.py")
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
    """Run the setup notice hook and return its (stdout, stderr)."""
    return _run(HELP_HOOK, state_home, payload, raw)


if __name__ == "__main__":
    unittest.main()
