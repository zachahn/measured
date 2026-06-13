---
name: plan
description: Design an architecture plan for a feature or bugfix, then break it into well-scoped, implementation-ready tickets.
disable-model-invocation: true
---

Create an agent team. The work runs in two phases: first design the architecture, then decompose it into tickets that reference the plan.

Both phases write into one **plan** — a directory holding the architecture plan and its tickets, persisted across sessions. Create it once, up front, and pass its path to every teammate:

- Run `measured-notes --new-plan-dir "<short description>"`. It prints the plan dir's absolute path, e.g. `.../2026-06-13-add-rate-limiting`.
- Give that full path to each subagent you spawn. They build their own files by joining filenames to it — `<plan-dir>/ARCHITECTURE.md`, `<plan-dir>/TASK-1.md`, and so on. Without it they cannot find the plan.

## Phase 1 — Architecture plan

1. Spawn a teammate using the subagent: `measured:plan-architect`. Tell it the plan dir path.
2. Wait for the draft. Then review it:
    - Spawn a teammate using the subagent: `measured:plan-architecture-reviewer`.
3. Ensure feedback is incorporated. Iterate until the architecture plan is sound.

## Phase 2 — Tickets

4. Spawn a teammate using the subagent: `measured:implementation-ticketing-tech-lead`. Tell it the plan dir path and that the architecture plan is done; it reads the plan and breaks it into tickets that reference it.
5. Wait for the draft. Then review it:
    - Spawn a teammate using the subagent: `measured:implementation-ticketing-review`.
    - Ask the architect to review the tickets against the architecture plan for cohesiveness — every ticket should trace back to the plan, and the tickets together should deliver it with no gaps.
6. Ensure feedback is incorporated. Iterate as necessary.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.
