---
name: brainstorming
description: "Two-phase design process: understand what to build, then plan how to build it."
disable-model-invocation: true
---

The user requested: $ARGUMENTS

## Required: user is in the loop

This skill is a collaboration with the user, not a solo run. You MUST stop and wait for the user's reply at every checkpoint below. Do not infer answers, do not pick on the user's behalf, do not advance phases on your own.

**Auto Mode does NOT override this.** Auto Mode lets you skip *clarifying* pauses where you'd otherwise check in out of caution. It does not authorize you to skip *required* user inputs. The checkpoints in this skill are required inputs: the spec and plan are wrong if the user didn't actually choose them.

If you ever find yourself about to "move immediately" past a checkpoint without a user message in between, stop. That is the bug this skill exists to prevent.

## Phase 1 — Understand the request

Use `Skill(measured:ticketing)` to fully understand the user's original request. That skill will collect clarifications and approach decisions from the user via `AskUserQuestion` and produce a confirmed ticket.

**Checkpoint:** After Phase 1 completes, present the finalized ticket/spec summary to the user and ask explicitly: "Ready to move to implementation planning?" Wait for the user's reply. Do not start Phase 2 until the user confirms.

## Phase 2 — Build the implementation plan

Use `Skill(measured:implementation-planning)` to create a thorough implementation plan.

**Checkpoint:** After Phase 2 completes, present the plan to the user and ask explicitly: "Ready to start implementation?" Wait for the user's reply. Do not start implementing until the user confirms.
