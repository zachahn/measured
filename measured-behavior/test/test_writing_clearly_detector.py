"""Tests for hooks/writing-clearly-detector.py — the Stop enforcement hook.

Run directly or via `rake test`. Stdlib unittest only.

Claude Code invokes the hook as `python3 .../writing-clearly-detector.py` with
the Stop payload on stdin. The payload carries `transcript_path`, a JSONL file
of the conversation. The hook reads Claude's last message from that file, runs
writing heuristics, and — only on a hit — prints a Stop hookSpecificOutput whose
additionalContext carries the guidance plus the flagged offenses. Clean text,
missing files, and junk input all produce no output.

We exercise the real subprocess entrypoint, writing a throwaway transcript per
case. The contract under test: exit 0 always; silence unless a heuristic fires;
each heuristic fires on its target; the em-dash/semicolon check never names the
punctuation in its output.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "writing-clearly-detector.py"
REMINDER = PLUGIN_ROOT / "hooks" / "writing-clearly-reminder.md"


def write_transcript(path, assistant_text):
    """Write a minimal JSONL transcript with one user and one assistant turn."""
    lines = [
        {"message": {"role": "user", "content": [{"type": "text", "text": "go"}]}},
        {"message": {"role": "assistant",
                     "content": [{"type": "text", "text": assistant_text}]}},
    ]
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n",
                    encoding="utf-8")


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def context_for(assistant_text):
    """Run the hook on a transcript holding `assistant_text`.

    Returns the injected additionalContext string, or None when the hook stays
    silent (clean text — no stdout).
    """
    with tempfile.TemporaryDirectory() as tmp:
        transcript = pathlib.Path(tmp) / "transcript.jsonl"
        write_transcript(transcript, assistant_text)
        proc = run_hook(json.dumps({"transcript_path": str(transcript)}))
        assert proc.returncode == 0, proc.stderr
        if not proc.stdout.strip():
            return None
        payload = json.loads(proc.stdout)
        return payload["hookSpecificOutput"]["additionalContext"]


# A block of prose carrying every sin at once: a noun-pile slogan, passive
# voice, a nominalization pile, comma overload, dense abstract nouns, and choppy
# punctuation. Kept domain-neutral on purpose — it reads like a design note for
# a generic report renderer.
FOGGY_SAMPLE = (
    "Renaming is the small part; the substance is that a step becomes authored "
    "code, absorbing iteration, pagination, and retries. "
    "The sandbox grants nothing ambient. Every call is mediated by the engine: "
    "budgeted, logged, taint-tracked. The layer's envelope, its boundary, and "
    "its invariant stay static. The clean resolution is one runtime mechanism, "
    "two authoring forms."
)


class SilenceTest(unittest.TestCase):
    def test_clean_prose_is_silent(self):
        clean = ("I renamed the step to ScriptStep. The engine now runs it as "
                 "code. The engine budgets, logs, and checks every call. The "
                 "tests pass.")
        self.assertIsNone(context_for(clean))

    def test_exits_zero_and_no_output_on_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = pathlib.Path(tmp) / "t.jsonl"
            write_transcript(transcript, "The parser reads the file. It works.")
            proc = run_hook(json.dumps({"transcript_path": str(transcript)}))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), "")


class MalformedInputTest(unittest.TestCase):
    def test_junk_stdin_is_silent(self):
        proc = run_hook("not even json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_empty_stdin_is_silent(self):
        proc = run_hook("")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_missing_transcript_path_is_silent(self):
        proc = run_hook(json.dumps({"other": "field"}))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_nonexistent_transcript_is_silent(self):
        proc = run_hook(json.dumps({"transcript_path": "/no/such/file.jsonl"}))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")


class OutputShapeTest(unittest.TestCase):
    def test_hit_emits_stop_event_with_guidance(self):
        context = context_for(FOGGY_SAMPLE)
        self.assertIsNotNone(context)
        # The guidance body from the reminder file rides along on every hit.
        reminder_body = REMINDER.read_text(encoding="utf-8").strip()
        first_rule = reminder_body.splitlines()[3]  # a rule bullet, not the tag
        self.assertIn(first_rule.strip(), context)

    def test_hit_lists_the_specific_offense(self):
        context = context_for(FOGGY_SAMPLE)
        self.assertIn("Flagged in your last message:", context)

    def test_stop_event_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = pathlib.Path(tmp) / "t.jsonl"
            write_transcript(transcript, FOGGY_SAMPLE)
            proc = run_hook(json.dumps({"transcript_path": str(transcript)}))
            payload = json.loads(proc.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"]["hookEventName"], "Stop")


class HeuristicTest(unittest.TestCase):
    def assertFlags(self, text, needle):
        context = context_for(text)
        self.assertIsNotNone(context, f"expected a flag for: {text!r}")
        self.assertIn(needle, context)

    def test_noun_pile_slogan(self):
        self.assertFlags(
            "The clean resolution is one runtime mechanism, two authoring forms.",
            "noun-pile slogan",
        )

    def test_passive_voice_with_agent(self):
        self.assertFlags(
            "Every call is mediated by the engine. It works well.",
            "passive voice",
        )

    def test_nominalization_pile(self):
        self.assertFlags(
            "Compilation failure results in deployment cessation.",
            "nominalization pile",
        )

    def test_comma_overload(self):
        self.assertFlags(
            "The step absorbs iteration, pagination, retries, and the glue.",
            "too many clauses",
        )

    def test_abstract_noun_density(self):
        self.assertFlags(
            "The envelope crosses the boundary. The handle wraps the sink. "
            "The trace records the invariant across the layer.",
            "too many abstract words",
        )

    def test_stacked_of_phrases(self):
        self.assertFlags(
            "It is a matter of degree of freedom that nobody planned.",
            'stacked "of" phrases',
        )


class SingleAbstractNounTest(unittest.TestCase):
    def test_one_abstract_noun_is_fine(self):
        # One abstract noun is normal writing. Density is the tell, not presence.
        self.assertIsNone(
            context_for("I moved the check to the call boundary. The tests pass.")
        )


class PunctuationSecrecyTest(unittest.TestCase):
    def test_em_dash_flags_without_naming_itself(self):
        context = context_for("The engine wins — the parser loses. That is it.")
        self.assertIsNotNone(context)
        self.assertIn("choppy punctuation", context)

    def test_semicolon_flags_without_naming_itself(self):
        context = context_for("The engine wins; the parser loses. That is it.")
        self.assertIsNotNone(context)
        self.assertIn("choppy punctuation", context)

    def test_flag_never_names_the_punctuation(self):
        # The whole point: never hand Claude the rule to game. The generated
        # offense line must describe the smell without naming the punctuation.
        # (The guidance body below it uses dashes freely — that is prose, not a
        # rule about dashes, so we only inspect the flag line.)
        context = context_for("The engine wins; the parser loses — done. Yes.")
        self.assertIsNotNone(context)
        flag_line = next(
            line for line in context.splitlines()
            if "choppy punctuation" in line
        )
        for banned in ("semicolon", "em-dash", "em dash", "emdash"):
            self.assertNotIn(banned, flag_line.lower())


if __name__ == "__main__":
    unittest.main()
