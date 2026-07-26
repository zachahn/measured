"""Tests for hooks/auto-approve-config.py — the measured-behavior-config approval hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../auto-approve-config.py`, so we
exercise that real entrypoint as a subprocess. The contract: exit 0 always; a
PreToolUse allow decision on stdout for a plain measured-behavior-config
invocation; empty stdout (no decision) for everything else.
"""

import json
import pathlib
import subprocess
import sys
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "auto-approve-config.py"


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

    def test_allows_bare_command(self):
        self.assert_allowed(run_hook(payload("Bash", "measured-behavior-config --list")))

    def test_allows_no_arguments(self):
        self.assert_allowed(run_hook(payload("Bash", "measured-behavior-config")))

    def test_allows_set(self):
        self.assert_allowed(
            run_hook(payload("Bash", "measured-behavior-config --set commit-behavior 'commit every turn'"))
        )

    def test_allows_path_to_bin(self):
        self.assert_allowed(
            run_hook(payload("Bash", "/Users/zach/Projects/measured/measured-behavior/bin/measured-behavior-config --list"))
        )

    def test_silent_on_chained_command(self):
        self.assert_no_decision(
            run_hook(payload("Bash", "measured-behavior-config --list; rm -rf /"))
        )

    def test_silent_on_piped_command(self):
        self.assert_no_decision(
            run_hook(payload("Bash", "measured-behavior-config --list | tee /tmp/x"))
        )

    def test_silent_on_and_chained_command(self):
        self.assert_no_decision(
            run_hook(payload("Bash", "measured-behavior-config --list && echo done"))
        )

    def test_silent_on_command_substitution(self):
        self.assert_no_decision(
            run_hook(payload("Bash", "measured-behavior-config --set commit-style $(cat /etc/hosts)"))
        )

    def test_silent_on_other_program(self):
        self.assert_no_decision(run_hook(payload("Bash", "echo measured-behavior-config")))

    def test_silent_on_lookalike_program_name(self):
        self.assert_no_decision(run_hook(payload("Bash", "not-measured-behavior-config --list")))

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
        self.assert_no_decision(run_hook(payload("Bash", "measured-behavior-config --set commit-style 'unterminated")))


if __name__ == "__main__":
    unittest.main()
