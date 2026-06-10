---
name: one-shot
description: Run the full cycle — orient, define, plan, build — in one session, keeping every gate.
disable-model-invocation: true
argument-hint: "[request]"
---

Run the four stages in order, carrying one slug through all of them. The stage skills sit beside this file under the base directory the harness announced; load each stage's `SKILL.md` with the `Read` tool — not `cat` or another shell command; only `Read` is pre-approved for plugin files — and follow it as if the user had invoked it. The `Skill` tool refuses these skills because they set `disable-model-invocation`.

1. `../orient/SKILL.md` — map the current state of the code.
2. `../define/SKILL.md` — pin the request down into `SPEC.md`.
3. `../plan/SKILL.md` — choose an approach and break it into steps.
4. `../build/SKILL.md` — execute the plan.

One-shot compresses the calendar, not the conversation. Every **GATE** in every stage still stops and asks the user. Enter each stage only after the previous stage's final gate passed.
