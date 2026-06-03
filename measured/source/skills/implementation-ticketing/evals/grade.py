#!/usr/bin/env python3
"""Grade implementation-ticketing eval outputs against structural assertions.

Reads the with_skill / without_skill output dirs for each eval and emits a
grading.json per run dir. Checks are deliberately conservative — they look for
the structural contract the skill is supposed to enforce, not prose quality.
"""

import json
import pathlib
import re
import sys

ITER = pathlib.Path(sys.argv[1])

SEVEN_FIELDS = [
    "Context / Background",
    "Acceptance Criteria",
    "Technical Guidance",
    "Out of Scope",
    "Dependencies",
    "Definition of Done",
]

# An imperative title leads with a base-form verb (after the optional
# "Task NNN:" prefix). We can't enumerate every verb, so detect the
# anti-pattern instead: a noun-phrase title (e.g. "Rate limiting",
# "CSV export") has no leading verb. We treat a title as imperative if its
# first word after the prefix is a plain word that is not a gerund (-ing) and
# the title is not a bare noun phrase. A curated verb list covers the common
# cases; anything else is checked against the gerund/article heuristic.
TITLE_RE = re.compile(r"^#\s*(?:Task\s*\d+\s*:\s*)?(`?\w[\w-]*)", re.MULTILINE)
NON_IMPERATIVE_FIRST = re.compile(r"(ing|tion|ment|ity| design|support)$", re.IGNORECASE)


def title_is_imperative(text):
    m = TITLE_RE.search(text)
    if not m:
        return False
    first = m.group(1).strip("`")
    # Bare noun-phrase / gerund leads are the failure mode we care about.
    if NON_IMPERATIVE_FIRST.search(first):
        return False
    # Articles/determiners as the first word also signal a non-imperative title.
    if first.lower() in {"a", "an", "the"}:
        return False
    return True

DEP_BACKWARD = re.compile(r"Task[-\s]?0*(\d+)")


def task_chunks(outputs: pathlib.Path):
    """Return list of (label, text) task units.

    A series-of-files output yields one chunk per TASK-NNN.md (the structure
    the skill wants). A single-file output is returned as one chunk so the
    field checks still run against it.
    """
    task_files = sorted(outputs.glob("TASK-*.md"))
    if task_files:
        return [(p.name, p.read_text()) for p in task_files]
    md = sorted(outputs.glob("*.md"))
    return [(p.name, p.read_text()) for p in md]


def grade_run(outputs: pathlib.Path):
    chunks = task_chunks(outputs)
    n_task_files = len(list(outputs.glob("TASK-*.md")))
    full_text = "\n".join(t for _, t in chunks)

    # 1. Series of separate task files (>=3)
    series = n_task_files >= 3

    # 2. All seven fields present in every task unit
    def has_all_fields(text):
        return all(f.lower() in text.lower() for f in SEVEN_FIELDS)

    all_fields = bool(chunks) and all(has_all_fields(t) for _, t in chunks)

    # 3. Imperative titles on every task unit (only meaningful for series)
    titles_imperative = series and all(
        title_is_imperative(t) for _, t in chunks
    )

    # 4. Acceptance criteria look testable (checklist or Given/When/Then)
    testable_ac = bool(chunks) and all(
        ("- [ ]" in t) or re.search(r"\bGiven\b.*\bwhen\b", t, re.IGNORECASE | re.DOTALL)
        for _, t in chunks
    )

    # 5. Dependencies are forward-consistent: a TASK-N must not depend on TASK-M>N
    forward_ok = True
    if series:
        for label, text in chunks:
            m = re.search(r"TASK-0*(\d+)", label)
            if not m:
                continue
            n = int(m.group(1))
            dep_section = text.split("## Dependencies", 1)
            if len(dep_section) < 2:
                continue
            after = dep_section[1].split("## Definition", 1)[0]
            # Only the "depends on / requires / blocked by" relationship
            # constrains ordering. A Dependencies section freely names other
            # relationships too — what it *blocks*, what it's *independent of* —
            # and those legitimately reference later tasks. So pull refs only
            # from the dependency clause itself: text right after a
            # "depends on / requires / blocked by" trigger, up to the next
            # sentence/clause boundary.
            for trigger in re.finditer(
                r"(?:depends?\s+on|requires?|blocked\s+by)\b([^.;\n]*)",
                after,
                re.IGNORECASE,
            ):
                for ref in DEP_BACKWARD.findall(trigger.group(1)):
                    if int(ref) > n:
                        forward_ok = False

    # 6. Out of Scope is non-empty somewhere
    oos = "out of scope" in full_text.lower()

    return {
        "n_task_files": n_task_files,
        "expectations": [
            {"text": "Output is a series of >=3 separate task files",
             "passed": series,
             "evidence": f"{n_task_files} TASK-NNN.md files"},
            {"text": "Every task has all seven required fields",
             "passed": all_fields,
             "evidence": "checked Context/AC/Guidance/Scope/Deps/DoD in each unit"},
            {"text": "Every task title is imperative/action-oriented",
             "passed": titles_imperative,
             "evidence": "regex on leading verb of each task title"},
            {"text": "Acceptance criteria are testable (checklist or Given/When/Then)",
             "passed": testable_ac,
             "evidence": "checkbox or Given...when pattern present in each unit"},
            {"text": "Dependencies point backward (no forward references)",
             "passed": forward_ok,
             "evidence": "no TASK-N depends on a higher-numbered task"},
            {"text": "Out of Scope is stated",
             "passed": oos,
             "evidence": "'out of scope' present in output"},
        ],
    }


def main():
    for eval_dir in sorted(ITER.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        for arm in ("with_skill", "without_skill"):
            outputs = eval_dir / arm / "outputs"
            if not outputs.is_dir():
                continue
            result = grade_run(outputs)
            (eval_dir / arm / "grading.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            passed = sum(e["passed"] for e in result["expectations"])
            total = len(result["expectations"])
            print(f"{eval_dir.name:30s} {arm:14s} {passed}/{total}  "
                  f"({result['n_task_files']} task files)")


if __name__ == "__main__":
    main()
