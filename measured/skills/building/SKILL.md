---
name: building
description: "Understand the request, create an implementation plan, then implement"
disable-model-invocation: true
---

## Collaborate with the user

Claude can never know the user's intent without asking. Proactively understand the problem and consider the solution; but never infer answers, never pick on the user's behalf, and never advance phases on your own.

Claude must collaborate with the user to create the optimal solution. Always stop and wait for the user's reply.

"Auto Mode" does not override this. "Auto Mode" will try to stop Claude from breaking the user's computer. "Auto Mode" still means Claude must collaborate.


## Phase 1 — Understand the request

Use `Skill(measured:ticketing)` to fully understand the user's original request.

## Phase 2 — Build the implementation plan

Use `Skill(measured:implementation-planning-beta)` to design the architecture and break it into tickets.

## Phase 3 — Implement

Use `Skill(measured:implementing-with-subagents)` to implement what we've planned.
