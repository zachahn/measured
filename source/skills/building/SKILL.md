---
name: building
description: "Understand the request, create an implementation plan, then implement"
disable-model-invocation: true
---

The user requested: $ARGUMENTS

## Required: user is in the loop

You must stop and wait for the user's reply. Never infer answers, never pick on the user's behalf, and never advance phases on your own. Claude must collaborate with the user to create the optimal solution.

"Auto Mode" does not override this; Auto Mode only affects permissions prompts. Note that "permissions" is different from "clarification".

## Phase 1 — Understand the request

Use `Skill(measured:ticketing)` to fully understand the user's original request.

## Phase 2 — Build the implementation plan

Use `Skill(measured:implementation-planning)` to create a thorough implementation plan.

## Phase 3 — Implement

Use `Skill(measured:implementing-with-subagents)` to implement what we've planned.
