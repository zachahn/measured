---
name: implementation-planning-beta
description: Draft a thorough implementation plan for feature development or bugfix.
disable-model-invocation: true
---

Create an agent team:

1. Spawn a teammate using the subagent: `measured:implementation-planning-architect`
2. Wait for the subagent to finish a draft. Afterwards, spawn subagents to review it.
    - Spawn a teammate using the subagent: `measured:implementation-planning-architecture-reviewer`
3. Spawn a teammate using the subagent: `measured:implementation-planning-engineer`
4. Wait for the subagent to finish a draft. Afterwards, spawn subagents to review it
    - Spawn a teammate using the subagent: `measured:implementation-planning-review`
    - Ask the architect to review the total plan and its cohesiveness.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication is expensive. Self-research, but be sure to escalate all questions and concerns to the user.
