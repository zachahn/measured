---
name: implementation-ticketing
description: Break a feature, epic, or bug into a series of well-scoped, implementation-ready engineering tasks
disable-model-invocation: true
---

Create an agent team:

1. Spawn a teammate using the subagent: `measured:implementation-ticketing-tech-lead`
2. Wait for the subagent to finish a draft. Afterwards, spawn subagents to review it:
    - Spawn a teammate using the subagent: `measured:implementation-ticketing-review`
    - Spawn a teammate to review the task series as an experienced engineer.
        - Enumerate the tasks with `measured-notes --task-list` and `Read` every `TASK-NNN.md` in order.
        - Verify each task is implementable with no blockers, and that the series as a whole — in order — actually delivers the feature.
3. Ensure feedback is incorporated. Iterate as necessary.

All sub-agents can and should ask the user for clarity.

Bad assumptions and miscommunication is expensive. Self-research, but be sure to escalate all questions and concerns to the user.
