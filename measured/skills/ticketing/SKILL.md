---
name: ticketing
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

The ticket lives in a **project** — a directory that persists across sessions. Allocate one up front and pass its reference to every teammate:

- Run `measured-notes --project-new`. It prints the project's directory, e.g. `.../PROJECT-0007`; the reference is its number (`7`).
- Give that reference to each subagent. They resolve the ticket with it — `measured-notes --ticket 7`.

Create an agent team:

1. Spawn a teammate using the subagent: `measured:ticketing-pm`. Tell it the project reference.
2. Wait for the subagent to finish a draft. Afterwards, spawn subagents to review it:
    - Spawn a teammate using the subagent: `measured:ticketing-review`. Tell it the project reference.
    - Spawn a teammate to review the ticket as an experienced engineer.
        - `Read` the ticket at the path printed by `measured-notes --ticket <project>`.
        - Verify that the ticket is implementable; that there is no ambiguity.
3. Ensure feedback is incorporated. Iterate as necessary.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication is expensive. Self-research, but be sure to escalate all questions and concerns to the user.
