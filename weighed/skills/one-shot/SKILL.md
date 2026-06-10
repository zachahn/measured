---
name: one-shot
description: Run the full cycle — orient, define, plan, build — in one session, keeping every gate.
disable-model-invocation: true
argument-hint: "[request]"
---

Run the four stages in order, carrying one slug through all of them:

1. `Skill(weighed:orient)` — map the current state of the code.
2. `Skill(weighed:define)` — pin the request down into `SPEC.md`.
3. `Skill(weighed:plan)` — choose an approach and break it into steps.
4. `Skill(weighed:build)` — execute the plan.

One-shot compresses the calendar, not the conversation. Every **GATE** in every stage still stops and asks the user. Enter each stage only after the previous stage's final gate passed.
