---
name: implementation-ticketing-review
---

Review the task series. Each task is its own `TASK-NNN.md` file. Run `measured-notes --task-list` to enumerate them, resolve any one to its path with `measured-notes --task-get <ref>`, and `Read` them all in numeric order. The goal: an engineer should be able to pick up any task and implement it with no blockers, and the series as a whole should actually deliver the feature.

Review as an experienced engineer who will own this work, not as a copy editor. A task series is good when the decomposition is sound — not when the prose is pretty.

<%= partials("reviewing_attention.md") %>

## What to check

**The series as a whole**

- **Ordering:** Does every dependency point backward? Could someone start at task 1 and proceed without hitting a forward reference?
- **Coverage:** Do the tasks together deliver the feature? What falls in the gaps between them? Name anything that no task owns.
- **Sizing:** Is any task secretly three tasks bundled together? Is any task too thin to merge on its own?
- **Seams:** Does each task leave the system in a working, mergeable state, or does it depend on a half-finished sibling?

**Each task** must have:

- **Title:** Imperative mood, action-oriented, specific.
- **Context / Background:** Why the task exists, in a sentence or three.
- **Acceptance Criteria:** Testable conditions. Could two engineers disagree about whether it's met? Then it's too vague — flag it.
- **Technical Guidance:** Useful pointers without over-prescribing. Flag both extremes: a task that reads like a line-by-line transcript (kills ownership) and a task with no pointers at all (forces the implementer to rediscover known gotchas).
- **Out of Scope:** Present where scope creep is plausible.
- **Dependencies:** Stated, or "None".
- **Definition of Done / Testing Notes:** Says how to test it; flags migrations, flags, rollback where relevant.

<%= partials("review_plan_cohesion.md") %>
