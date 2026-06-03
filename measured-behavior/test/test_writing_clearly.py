"""Tests for hooks/writing-clearly.py — the SessionStart guidance hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../writing-clearly.py`, so we exercise
that real entrypoint as a subprocess rather than importing it. The contract the
harness depends on is narrow: exit 0, valid JSON on stdout, the guidance carried
verbatim in hookSpecificOutput.additionalContext, and stdin ignored.
"""

import json
import pathlib
import subprocess
import sys
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "writing-clearly.py"
GUIDANCE = PLUGIN_ROOT / "hooks" / "writing-clearly.md"


def run_hook(stdin_text=""):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


class WritingClearlyHookTest(unittest.TestCase):
    def test_exits_zero(self):
        proc = run_hook()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_emits_valid_json(self):
        # json.loads raises on malformed output, failing the test.
        json.loads(run_hook().stdout)

    def test_session_start_shape(self):
        payload = json.loads(run_hook().stdout)
        hook_out = payload["hookSpecificOutput"]
        self.assertEqual(hook_out["hookEventName"], "SessionStart")
        self.assertIn("additionalContext", hook_out)

    def test_injects_guidance_verbatim(self):
        payload = json.loads(run_hook().stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["additionalContext"],
            GUIDANCE.read_text(encoding="utf-8"),
        )

    def test_ignores_stdin(self):
        # The SessionStart payload varies (startup/resume/clear/compact) but
        # never changes what we inject. Arbitrary stdin — a real payload, junk,
        # or nothing — must produce the same output.
        real = run_hook('{"hook_event_name": "SessionStart", "source": "resume"}').stdout
        junk = run_hook("not even json").stdout
        empty = run_hook("").stdout
        self.assertEqual(real, junk)
        self.assertEqual(junk, empty)


if __name__ == "__main__":
    unittest.main()
