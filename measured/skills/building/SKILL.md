---
name: building
description: "Understand the request, create an implementation plan, then implement"
disable-model-invocation: true
---

## Collaborate with the user

Claude can never know the user's intent without asking. Proactively understand the problem and consider the solution; but never infer answers, never pick on the user's behalf, and never advance phases on your own.

Claude must collaborate with the user to create the optimal solution. Always stop and wait for the user's reply.

"Auto Mode" does not override this. "Auto Mode" will try to stop Claude from breaking the user's computer. "Auto Mode" still means Claude must collaborate.

Each phase below sits in a sibling skill beside this file under the base directory the harness announced. Load each phase's `SKILL.md` with the `Read` tool — not `cat` or another shell command; only `Read` is pre-approved for plugin files — and follow it as if the user had invoked it. The `Skill` tool refuses these skills because they set `disable-model-invocation`.

## Phase 1 — Understand the request

Read `../ticketing/SKILL.md` and follow it to fully understand the user's original request.

## Phase 2 — Build the implementation plan

Read `../implementation-planning/SKILL.md` and follow it to design the architecture and break it into tickets.

## Phase 3 — Implement

Read `../implementing-with-subagents/SKILL.md` and follow it to implement what we've planned.
