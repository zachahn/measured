#!/usr/bin/env python3
"""Normalize writing-clearly judge verdicts into the eval harness schema.

Prose quality doesn't reduce to regex, so the subjective scoring is done by a
judge agent (see judge.md) that reads each arm's prose and writes a verdict.json
scoring every rubric rule 0-2. This script is the deterministic half: it reads
those verdicts, applies a fixed pass threshold in ONE place (so runs stay
comparable as the judge prompt evolves), enforces that the judge covered every
rule, and writes the grading.json that `rake eval:benchmark` consumes.

Layout per run:
    <iteration>/eval-*/<arm>/outputs/      prose written by the author
    <iteration>/eval-*/<arm>/verdict.json  scores from the judge agent
    <iteration>/eval-*/<arm>/grading.json  written here

Usage:  python3 grade.py <iteration-dir>

Stdlib only.
"""

import json
import pathlib
import sys

ITER = pathlib.Path(sys.argv[1])
RUBRIC_PATH = pathlib.Path(__file__).resolve().parent / "evals.json"

# A rule passes only on a clean 2. Adherence is the whole point of the guidance,
# so a 1 ("mixed") is a partial violation and does not pass. Drop to 1 for a
# more permissive bar — but keep it in this one place so iterations compare.
PASS_SCORE = 2

ARMS = ("with_skill", "without_skill")


def load_rubric():
    return json.loads(RUBRIC_PATH.read_text())["rubric"]


def grade_run(verdict, rubric):
    by_id = {r.get("id"): r for r in verdict.get("rules", [])}
    expectations = []
    for rule in rubric:
        scored = by_id.get(rule["id"])
        if scored is None:
            # The judge skipped a rule. Fail it loudly rather than drop it and
            # inflate the pass rate.
            expectations.append({
                "text": rule["rule"],
                "passed": False,
                "evidence": "judge did not score this rule",
            })
            continue
        score = scored.get("score")
        evidence = str(scored.get("evidence", "")).strip()
        expectations.append({
            "text": rule["rule"],
            "passed": isinstance(score, int) and score >= PASS_SCORE,
            "evidence": f"score {score}/2 — {evidence}",
        })
    return {
        "expectations": expectations,
        "notes": [verdict["notes"]] if verdict.get("notes") else [],
    }


def main():
    rubric = load_rubric()
    found = False
    for eval_dir in sorted(ITER.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        for arm in ARMS:
            verdict_path = eval_dir / arm / "verdict.json"
            if not verdict_path.is_file():
                continue
            found = True
            verdict = json.loads(verdict_path.read_text())
            result = grade_run(verdict, rubric)
            (eval_dir / arm / "grading.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            passed = sum(e["passed"] for e in result["expectations"])
            total = len(result["expectations"])
            print(f"{eval_dir.name:34s} {arm:14s} {passed}/{total}")
    if not found:
        sys.exit(
            f"no eval-*/<arm>/verdict.json found under {ITER} — "
            "run the judge agent first (see evals/README.md)"
        )


if __name__ == "__main__":
    main()
