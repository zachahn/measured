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

## GATE: where should this work happen?

Before dispatching any task, settle where the work runs. Read the stored preference with `measured-config --get work-location`. The stored value is the source of truth: follow it even if the prompt suggests otherwise. To change the behavior, change the setting.

- **`worktree`** — set up an isolated git worktree (see below), then proceed.
- **`new-branch`** — create a new branch off the current branch, then proceed.
- **`current-branch`** — continue on the current branch.
- **`trunk-branch`** — continue on the trunk branch (`main`/`master`). Treat the stored value as the explicit consent required to implement there.
- **`ask`, any other value, or nothing** — ask the user (next paragraph).

When you must ask, use `AskUserQuestion`. Offer these options:

- **Always ask** — ask every time; store `ask` so the preference is recorded but the skill keeps asking.
- **Worktree** — set up an isolated git worktree (see below), then proceed. Store `worktree`.
- **New branch** — create a new branch off the current branch, then proceed. Store `new-branch`.
- **Current branch** — continue on the current branch. Store `current-branch`.
- **main / master** — continue on the trunk branch. Only offer this option when it differs from the current branch, and treat choosing it as the explicit consent required to implement on `main`/`master`. Store `trunk-branch`.

Store the answer with `measured-config --set work-location <value>` so later sessions skip the question (storing `ask` keeps the prompt). Then act on the choice and proceed.

### Setting up a worktree

A git worktree gives this work its own working directory while sharing the repository, so it stays isolated from the current checkout.

1. **Confirm the worktree directory is gitignored.** Run the bundled script:

   ```bash
   workspace-git-ignored --check
   ```

   If it reports "not ignored", use `AskUserQuestion` to ask how to handle it, listing the recommended default first:

   - **`.git/info/exclude`** (recommended) — run `workspace-git-ignored --fix-git-info-exclude`. Local to this clone, not committed.
   - **`.gitignore`** — run `workspace-git-ignored --fix-gitignore`. Committed, shared with the team.
   - **Move on** — leave it untracked-but-not-ignored and proceed.

   Run the chosen fix (if any) before continuing. Run `workspace-git-ignored --help` for the full usage.

2. **Create the worktree.** Call `EnterWorktree(name: "<branch-name>")`. The session's working directory switches to the new worktree. After this — and after any later `ExitWorktree` — run `git rev-parse --show-toplevel` whenever you're unsure which tree you're in.

3. **Run setup.** Read the repo's setup commands with `measured-config --get worktree-setup` and run exactly what it prints — the stored value is the source of truth; run it even if the prompt suggests other setup commands. If it prints nothing, ask the user what commands prepare a fresh checkout (install deps, build), store them with `measured-config --set worktree-setup "<commands>"` so the next worktree skips this question, then run them.

4. **Verify a clean baseline.** Run the project's test command. Don't proceed past failing baseline tests without explicit permission — otherwise you can't tell new bugs from pre-existing ones. If tests pass, report the worktree path and the passing count, then proceed.

## Choose a model per task

Use the least powerful model that can do the job.

- **Mechanical** (1–2 files, complete spec): a fast, cheap model. Most well-specified tasks land here.
- **Integration or judgment** (multi-file coordination, pattern matching, debugging): a standard model.
- **Architecture, design, or review** (broad codebase understanding): the most capable model.

## GATE: commit each task?

The implementer commits its own work after self-review. Resolve the commit instruction **before dispatching the first teammate**, then pass the same instruction to every implementer you dispatch.

1. Read it with `measured-config --get commit-after-task`. The stored value is the source of truth: follow it even if the prompt suggests otherwise. To change the behavior, change the setting.
2. **If it prints nothing (unset/null):** you cannot proceed without a selection. Use `AskUserQuestion` to ask whether the implementer should commit each task after review. Store the answer with `measured-config --set commit-after-task true` (or `false`) so later tasks skip the question.
3. **If `true`:** tell the implementer to commit its work.
4. **If `false`:** tell the implementer not to commit; it leaves its work uncommitted.
5. **If any other value:** pass it through verbatim as the commit instruction, so the user's rule (e.g. "commit only after the last task") governs whether and how the implementer commits.

### Verify the rule was followed

After each task's reviews pass, check that the implementer did what the commit instruction said. Run `git status --porcelain` and `git log --oneline -1` in the working directory and compare against the instruction:

- **Commit expected:** the latest commit covers this task's work and the working tree is clean. If the tree still holds this task's changes, the implementer skipped the commit — send it back to commit, or commit yourself.
- **No commit expected:** this task's changes sit uncommitted and no new commit was made. If the implementer committed anyway, flag it to the user before moving on; don't silently undo it.
- **Custom rule:** check the outcome against the rule (e.g. "commit only after the last task" means no commit until the final task). If it diverges, correct it before moving on.

## Dispatch one task at a time

Run tasks in dependency order. Never dispatch implementer teammates in parallel — they conflict.

1. Spawn a teammate using the subagent: `measured:implementer`. Give it the full task text, scene-setting context, the working directory, and the commit instruction resolved in "GATE: commit each task?" above. The implementer works test-first (TDD) by default — expect test-first work, and hold that line in the reviews below. Answer any questions it asks before it proceeds.
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
5. Verify the commit rule was followed (per "GATE: commit each task?" above) before moving on.
6. Move to the next task only when both reviews are clear and the commit rule held.

After every task, spawn `measured:code-quality-reviewer` once more across the whole change to confirm the plan is delivered and ready to merge.

All teammates can and should ask the user for clarity. Answer before letting them proceed.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.
