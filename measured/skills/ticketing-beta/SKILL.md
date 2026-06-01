---
name: ticketing-beta
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

Create an agent team:

1. Spawn a teammate using the subagent: `measured:ticketing-pm`
2. Wait for the subagent to finish a draft. Afterwards, spawn subagents to review it:
    - Spawn a teammate using the subagent: `measured:ticketing-review`
    - Spawn a teammate to review the ticket as an experienced engineer.
        - `Read` the ticket at the path printed by `measured-session-dir --ticket`.
        - Verify that the ticket is implementable; that there is no ambiguity.
3. Ensure feedback is incorporated. Iterate as necessary.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication is expensive. Self-research, but be sure to escalate all questions and concerns to the user.
