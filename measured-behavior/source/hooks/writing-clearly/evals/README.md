# writing-clearly eval

`writing-clearly` is a SessionStart hook, not a skill — so this eval measures
whether the injected guidance (`hooks/writing-clearly.md`) makes Claude's prose
follow *Elements of Style*. The harness is the same one skills use
(`with_skill` / `without_skill` arms → `grading.json` → `rake eval:benchmark` →
viewer); only two things differ:

1. **The "treatment" is the injected text, not a loaded skill.** The
   `with_skill` arm prepends the full contents of `hooks/writing-clearly.md` to
   the author's context — exactly what the hook does at session start. The
   `without_skill` arm omits it. The task prompt is identical across arms.
2. **The grader is a judge agent, not regex.** "Avoid adverbs", "omit needless
   words", and "concrete nouns" don't reduce to patterns, so a judge scores each
   rule (`judge.md`). `grade.py` then turns the judge's scores into the
   harness's `grading.json` schema.

## Files (committed)

- `evals.json` — the task prompts and the shared five-rule `rubric`. Single
  source of truth for both the judge and `grade.py`.
- `judge.md` — the judge agent's instructions: read one arm's prose, score every
  rubric rule 0–2 with quoted evidence, write `verdict.json`.
- `grade.py` — reads each arm's `verdict.json`, applies the pass threshold
  (`PASS_SCORE`), and writes `grading.json`. Stdlib only.

## Running an iteration

Eval runs are scratch — put them under `writing-clearly-workspace/iteration-N/`
(matches the `*-workspace/` gitignore; don't commit them).

Per the project CLAUDE.md, a test subagent can't reliably spawn its own team, so
have each run act as the primary author and write its prose directly into the
output dir — no `AskUserQuestion`, no further subagents, no session-only CLIs.

For each eval in `evals.json`, and for each arm:

1. **Author the prose.** Give a fresh author only the eval's `prompt`. For the
   `with_skill` arm, prepend the contents of `hooks/writing-clearly.md` to that
   prompt; for `without_skill`, don't. Write the result to:

   ```
   iteration-N/eval-<id>-<name>/<arm>/outputs/answer.md
   ```

2. **Judge it.** Give a judge agent `judge.md` + the `rubric` from `evals.json`,
   pointed at that arm's `outputs/`. The judge is blind to the arm. It writes:

   ```
   iteration-N/eval-<id>-<name>/<arm>/verdict.json
   ```

3. **Capture timing** (optional) from the author's completion notification into
   `iteration-N/eval-<id>-<name>/<arm>/timing.json`
   (`{"total_duration_seconds": ..., "total_tokens": ...}`).

Then grade and aggregate:

```sh
python3 measured-behavior/source/hooks/writing-clearly/evals/grade.py \
  measured-behavior/source/hooks/writing-clearly-workspace/iteration-N
rake eval:benchmark[measured-behavior/source/hooks/writing-clearly-workspace/iteration-N,writing-clearly]
```

Review with skill-creator's viewer:

```sh
python3 <skill-creator>/eval-viewer/generate_review.py \
  <iteration-dir> --benchmark <iteration-dir>/benchmark.json
```

## Reading the result

The signal is the **`delta` in mean `pass_rate`** between arms (`with_skill`
minus `without_skill`). The effect is small — five lines of widely-agreed style
advice — and prose grading is noisy, so run several trials per arm before
trusting a delta. To make the bar stricter or looser, change `PASS_SCORE` in
`grade.py` (one place, so iterations stay comparable).

To reduce judge bias, consider running the judge on a shuffled, arm-stripped
copy of the outputs so it can't infer which arm it's scoring.
