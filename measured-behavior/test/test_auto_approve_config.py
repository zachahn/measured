"""Tests for hooks/auto-approve-config.py, the measured-behavior-config approval hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../auto-approve-config.py`, so we
exercise that real entrypoint as a subprocess. The contract: exit 0 always; a
PreToolUse allow decision on stdout for a plain measured-behavior-config
invocation; empty stdout (no decision) for everything else.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "auto-approve-config.py"
PLUGIN_BIN = PLUGIN_ROOT / "bin" / "measured-behavior-config"


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def payload(tool_name, command):
    return json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
    })


class AutoApproveConfigTest(unittest.TestCase):
    def assert_no_decision(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    def assert_allowed(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "allow")

    def assert_command_allowed(self, command):
        self.assert_allowed(run_hook(payload("Bash", command)))

    def assert_command_silent(self, command):
        self.assert_no_decision(run_hook(payload("Bash", command)))

    # Invocations the hook exists to approve.

    def test_allows_bare_command(self):
        self.assert_command_allowed("measured-behavior-config --list")

    def test_allows_no_arguments(self):
        self.assert_command_allowed("measured-behavior-config")

    def test_allows_set(self):
        self.assert_command_allowed(
            "measured-behavior-config --set commit-behavior 'commit every turn'"
        )

    def test_allows_get(self):
        self.assert_command_allowed("measured-behavior-config --get commit-style")

    def test_allows_unset(self):
        self.assert_command_allowed("measured-behavior-config --unset commit-style")

    def test_allows_help(self):
        self.assert_command_allowed("measured-behavior-config --help")
        self.assert_command_allowed("measured-behavior-config -h")

    def test_allows_absolute_path_to_plugin_bin(self):
        self.assert_command_allowed(f"{PLUGIN_BIN} --list")

    def test_allows_symlink_to_plugin_bin(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = pathlib.Path(tmp) / "measured-behavior-config"
            os.symlink(PLUGIN_BIN, link)
            self.assert_command_allowed(f"{link} --list")

    # Shell operators that chain a second command onto the first.

    def test_silent_on_chained_command(self):
        self.assert_command_silent("measured-behavior-config --list; rm -rf /")

    def test_silent_on_piped_command(self):
        self.assert_command_silent("measured-behavior-config --list | tee /tmp/x")

    def test_silent_on_and_chained_command(self):
        self.assert_command_silent("measured-behavior-config --list && echo done")

    def test_silent_on_command_substitution(self):
        self.assert_command_silent(
            "measured-behavior-config --set commit-style $(cat /etc/hosts)"
        )

    def test_silent_on_newline_chained_command(self):
        # bash separates commands on a newline exactly as it does on `;`, and
        # shlex.split drops a newline as ordinary whitespace.
        self.assert_command_silent("measured-behavior-config --list\nrm -rf /tmp/x")

    def test_silent_on_backslash_newline_chained_command(self):
        self.assert_command_silent("measured-behavior-config --list\\\nrm -rf /tmp/x")

    def test_silent_on_carriage_return_chained_command(self):
        self.assert_command_silent("measured-behavior-config --list\rrm -rf /tmp/x")

    def test_silent_on_redirect(self):
        self.assert_command_silent("measured-behavior-config --list > /tmp/x")

    def test_silent_on_background_operator(self):
        self.assert_command_silent("measured-behavior-config --list & rm -rf /tmp/x")

    def test_silent_on_process_substitution(self):
        self.assert_command_silent("measured-behavior-config --get <(rm -rf /tmp/x)")

    def test_silent_on_backtick_substitution(self):
        self.assert_command_silent("measured-behavior-config --get `id`")

    # A program that is not this plugin's own copy of the command.

    def test_silent_on_other_program(self):
        self.assert_command_silent("echo measured-behavior-config")

    def test_silent_on_lookalike_program_name(self):
        self.assert_command_silent("not-measured-behavior-config --list")

    def test_silent_on_relative_path(self):
        self.assert_command_silent("./measured-behavior-config --list")

    def test_silent_on_traversal_path(self):
        self.assert_command_silent("../../../tmp/evil/measured-behavior-config --list")

    def test_silent_on_absolute_path_elsewhere(self):
        self.assert_command_silent("/tmp/evil/measured-behavior-config --list")

    def test_silent_on_tilde_path(self):
        self.assert_command_silent("~/evil/measured-behavior-config --list")

    # Arguments outside the command's real grammar.

    def test_silent_on_unknown_flag(self):
        self.assert_command_silent("measured-behavior-config --exec rm")

    def test_silent_on_unknown_key(self):
        self.assert_command_silent("measured-behavior-config --get not-a-real-key")
        self.assert_command_silent("measured-behavior-config --set not-a-real-key x")

    def test_silent_on_wrong_arity(self):
        self.assert_command_silent("measured-behavior-config --set commit-style")
        self.assert_command_silent("measured-behavior-config --get commit-style extra")
        self.assert_command_silent("measured-behavior-config --list extra")

    def test_silent_on_positional_argument(self):
        self.assert_command_silent("measured-behavior-config commit-style")

    # Malformed input to the hook itself.

    def test_silent_on_other_tools(self):
        self.assert_no_decision(run_hook(json.dumps({
            "tool_name": "Read",
            "tool_input": {"file_path": "measured-behavior-config"},
        })))

    def test_silent_on_missing_command(self):
        self.assert_no_decision(run_hook(json.dumps({"tool_name": "Bash", "tool_input": {}})))

    def test_silent_on_junk_stdin(self):
        self.assert_no_decision(run_hook("not even json"))
        self.assert_no_decision(run_hook(""))

    def test_silent_on_unbalanced_quotes(self):
        self.assert_command_silent(
            "measured-behavior-config --set commit-style 'unterminated"
        )


if __name__ == "__main__":
    unittest.main()
