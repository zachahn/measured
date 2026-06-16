---
name: implement
description: Use when executing implementation plans with independent tasks in the current session
disable-model-invocation: true
---

Execute a plan one task at a time, dispatching a fresh subagent per task. You are the controller: you read the tasks, curate context, dispatch teammates, and gate each task through two reviews before moving on.

You work from a **plan dir** — the directory holding the plan's files, which persists across sessions.

- If you were given a plan dir path or a `TICKET.md` path, use that dir.
- Otherwise, run `measured-notes` (no arguments) to print this repo's state dir, then list its `YYYY-MM-DD-slug` plan dirs and pick the one the user means.

Build each file's path by joining its filename to the plan dir:

- List the dir's `TASK-N.md` files (Glob/`ls`) to enumerate the tasks; their numbers run in dependency order.
- A task's path is `<plan-dir>/TASK-N.md`.
- The architecture plan is `<plan-dir>/ARCHITECTURE.md`.

Read the architecture plan and every task yourself. Paste each task's full text and its scene-setting context into the teammate's prompt — never make a teammate resolve or read its own task file.

Never start implementation on `main`/`master` without explicit user consent.

## Choose a model per task

Use the least powerful model that can do the job.

- **Mechanical** (1–2 files, complete spec): a fast, cheap model. Most well-specified tasks land here.
- **Integration or judgment** (multi-file coordination, pattern matching, debugging): a standard model.
- **Architecture, design, or review** (broad codebase understanding): the most capable model.

## Dispatch one task at a time

Run tasks in dependency order. Never dispatch implementer teammates in parallel — they conflict.

1. Spawn a teammate using the subagent: `measured:implementer`. Give it the full task text, scene-setting context, and the working directory. Answer any questions it asks before it proceeds.
2. Handle its reported status:
    - **DONE:** proceed to review.
    - **DONE_WITH_CONCERNS:** read the concerns. Address those about correctness or scope before review; note observations and proceed.
    - **NEEDS_CONTEXT:** provide the missing context and re-dispatch.
    - **BLOCKED:** assess the blocker — provide more context, re-dispatch with a more capable model, break the task into smaller pieces, or escalate to the user if the plan is wrong. Never force the same model to retry unchanged.
3. Review for spec compliance first:
    - Spawn a teammate using the subagent: `measured:spec-reviewer`. Give it the task requirements and the implementer's report.
    - If it finds issues, the same implementer fixes them, then the reviewer reviews again. Repeat until ✅.
4. Review code quality second — only after spec compliance is ✅:
    - Spawn a teammate using the subagent: `measured:code-quality-reviewer`. Give it the implementer's report, the task reference, the base and head SHAs, and a task summary.
    - If it finds issues, the same implementer fixes them, then the reviewer reviews again. Repeat until approved.
5. Move to the next task only when both reviews are clear.

After every task, spawn `measured:code-quality-reviewer` once more across the whole change to confirm the plan is delivered and ready to merge.

All teammates can and should ask the user for clarity. Answer before letting them proceed.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.
