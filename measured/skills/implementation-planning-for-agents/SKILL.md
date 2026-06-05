---
name: implementation-planning-for-agents
description: Design an architecture plan for a feature or bugfix, then break it into well-scoped, implementation-ready tickets for coding agents to pick up.
disable-model-invocation: true
---

Create an agent team. The work runs in two phases: first design the architecture, then decompose it into tickets that reference the plan.

Both phases write into one **project** — a directory holding the architecture plan and its tickets, persisted across sessions. Allocate it once, up front, and pass its reference to every teammate:

- Run `measured-notes --project-new`. It prints the project's directory, e.g. `.../PROJECT-0007`; the reference is its number (`7`).
- Give that reference to each subagent you spawn. They resolve their own files with it — `measured-notes --architecture 7`, `measured-notes --task-new 7`, and so on. Without it they cannot find the plan.

## Phase 1 — Architecture plan

1. Spawn a teammate using the subagent: `measured:implementation-planning-architect`. Tell it the project reference.
2. Wait for the draft. Then review it:
    - Spawn a teammate using the subagent: `measured:implementation-planning-architecture-reviewer`.
3. Ensure feedback is incorporated. Iterate until the architecture plan is sound.

## Phase 2 — Tickets

4. Spawn a teammate using the subagent: `measured:implementation-ticketing-tech-lead-for-agents`. Tell it the project reference and that the architecture plan is done; it reads the plan and breaks it into tickets that reference it.
5. Wait for the draft. Then review it:
    - Spawn a teammate using the subagent: `measured:implementation-ticketing-review`.
    - Ask the architect to review the tickets against the architecture plan for cohesiveness — every ticket should trace back to the plan, and the tickets together should deliver it with no gaps.
6. Ensure feedback is incorporated. Iterate as necessary.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.
