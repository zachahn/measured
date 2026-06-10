"""Tests for hooks/auto-approve-plugin-reads.py — the weighed read-approval hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../auto-approve-plugin-reads.py`, so
we exercise that real entrypoint as a subprocess. The contract: exit 0 always;
a PreToolUse allow decision on stdout for Read targets inside the plugin root;
empty stdout (no decision) for everything else.
"""

import json
import pathlib
import subprocess
import sys
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "auto-approve-plugin-reads.py"
SKILL_INSIDE = PLUGIN_ROOT / "skills" / "orient" / "SKILL.md"


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def payload(tool_name, file_path):
    return json.dumps({
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    })


class AutoApprovePluginReadsTest(unittest.TestCase):
    def assert_no_decision(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_allows_read_inside_plugin(self):
        proc = run_hook(payload("Read", str(SKILL_INSIDE)))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "allow")

    def test_allows_relative_sibling_read(self):
        # The path shape one-shot produces: ../<stage>/SKILL.md from a skill dir.
        path = PLUGIN_ROOT / "skills" / "one-shot" / ".." / "plan" / "SKILL.md"
        proc = run_hook(payload("Read", str(path)))
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "allow")

    def test_silent_on_read_outside_plugin(self):
        self.assert_no_decision(run_hook(payload("Read", "/etc/hosts")))

    def test_silent_on_traversal_out_of_plugin(self):
        escaped = PLUGIN_ROOT / "skills" / ".." / ".." / "measured" / "README.md"
        self.assert_no_decision(run_hook(payload("Read", str(escaped))))

    def test_silent_on_other_tools(self):
        self.assert_no_decision(run_hook(payload("Edit", str(SKILL_INSIDE))))
        self.assert_no_decision(run_hook(payload("Write", str(SKILL_INSIDE))))

    def test_silent_on_missing_file_path(self):
        self.assert_no_decision(run_hook(json.dumps({"tool_name": "Read", "tool_input": {}})))

    def test_silent_on_junk_stdin(self):
        self.assert_no_decision(run_hook("not even json"))
        self.assert_no_decision(run_hook(""))


if __name__ == "__main__":
    unittest.main()
