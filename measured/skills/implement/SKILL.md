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

Read the architecture plan and every task yourself. You are the only one who reads these files: each teammate gets its task pasted into its prompt, never a path to resolve.

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

Pass the model to each spawn with `Agent(subagent_type: "general-purpose", model: "<model>")`. Use the least powerful model that can do the job.

- **Mechanical** (1–2 files, complete spec): `haiku`. Most well-specified tasks land here.
- **Integration or judgment** (multi-file coordination, pattern matching, debugging): `sonnet`.
- **Architecture or design** (broad codebase understanding): `opus`.

## GATE: commit each task?

The implementer commits its own work after self-review. Resolve the commit instruction **before dispatching the first teammate**, then pass the same instruction to every implementer you dispatch.

1. Read it with `measured-config --get commit-behavior`. The stored value is the source of truth: follow it even if the prompt suggests otherwise. To change the behavior, change the setting.
2. **If it prints nothing (unset/null):** you cannot proceed without a selection. Use `AskUserQuestion` to ask whether the implementer should commit each task after review. Store the answer with `measured-config --set commit-behavior after-every-turn` (or `on-user-request`) so later tasks skip the question.
3. **If `after-every-turn`:** tell the implementer to commit its work.
4. **If `on-user-request`:** tell the implementer not to commit; it leaves its work uncommitted.
5. **If any other value:** pass it through verbatim as the commit instruction, so the user's rule (e.g. "commit only after the last task") governs whether and how the implementer commits.

Also read `measured-config --get commit-location`, `--get commit-style`, `--get commit-scope`, `--get commit-body`, and `--get commit-claude-attribution`. Pass every value that prints to the implementer alongside the commit instruction, so its commits match the rest of the repo. Skip any that print nothing.

### Verify the rule was followed

After each task's reviews pass, check that the implementer did what the commit instruction said. Run `git status --porcelain` and `git log --oneline -1` in the working directory and compare against the instruction:

- **Commit expected:** the latest commit covers this task's work and the working tree is clean. If the tree still holds this task's changes, the implementer skipped the commit — send it back to commit, or commit yourself.
- **No commit expected:** this task's changes sit uncommitted and no new commit was made. If the implementer committed anyway, flag it to the user before moving on; don't silently undo it.
- **Custom rule:** check the outcome against the rule (e.g. "commit only after the last task" means no commit until the final task). If it diverges, correct it before moving on.

## Dispatch one task at a time

Run tasks in dependency order. Never dispatch implementer teammates in parallel — they conflict.

1. Spawn a teammate:

    ```
    Agent(subagent_type: "general-purpose",
          model: "<model>",
          name: "implement-task-N",
          description: "Implement task N",
          prompt: "<the brief>")
    ```

    Always pass `name`. The review steps send fixes back to this same agent by name, and an unnamed agent can only be reached by its raw ID.

    Build the prompt from the template in "The implementer's brief" below: the full task text, scene-setting context, the working directory, and the commit instruction resolved in "GATE: commit each task?" above. A general-purpose agent starts with none of this, so paste the whole brief rather than summarizing it. Answer any questions it asks before it proceeds.
2. Handle its reported status:
    - **DONE:** proceed to review.
    - **DONE_WITH_CONCERNS:** read the concerns. Address those about correctness or scope before review; note observations and proceed.
    - **NEEDS_CONTEXT:** send the missing context with `SendMessage`, which resumes the same agent rather than starting it over.
    - **BLOCKED:** assess the blocker. Send more context, spawn a fresh agent on a more capable model, break the task into smaller pieces, or escalate to the user if the plan is wrong. Never force the same model to retry unchanged. When you do move to a stronger model, spawn a new agent under a new name and use that name for the rest of this task.
3. Review for spec compliance first:
    - Spawn a teammate using the subagent: `measured:spec-reviewer`. Give it the task requirements and the implementer's report.
    - If it finds issues, send them to the same implementer with `SendMessage(to: "implement-task-N", ...)`, which resumes it with its context intact. Spawning a fresh agent would lose everything it learned. Then re-review. Repeat until ✅.
4. Review code quality second — only after spec compliance is ✅:
    - Spawn a teammate using the subagent: `measured:code-quality-reviewer`. Give it the implementer's report, the task reference, the base and head SHAs, and a task summary.
    - If it finds issues, send them to the same implementer with `SendMessage(to: "implement-task-N", ...)`, then re-review. Repeat until approved.
5. Verify the commit rule was followed (per "GATE: commit each task?" above) before moving on.
6. Move to the next task only when both reviews are clear and the commit rule held.

After every task, spawn `measured:code-quality-reviewer` once more across the whole change to confirm the plan is delivered and ready to merge.

All teammates can and should ask the user for clarity. Answer before letting them proceed.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.

## The implementer's brief

Send this to each `general-purpose` teammate, filling in the four bracketed slots. Send it whole. The agent has no other source for these rules, and a summary drops the parts that keep it honest.

---

Implement a single, testable task.

**Task:** [paste the full text of `TASK-N.md` — never make the teammate read its own task file]

**Context:** [where this fits, its dependencies, the architectural context from `ARCHITECTURE.md`]

**Working directory:** [absolute path]

**Commit instruction:** [the instruction resolved in the commit gate, plus every commit setting that printed a value]

### Before you begin

Ask now about anything unclear in the requirements, the approach, the dependencies, or the acceptance criteria. Raise concerns before starting work, not after.

### Your job

1. Implement exactly what the task specifies, test-first.
2. Verify it works.
3. Self-review.
4. Commit, unless the commit instruction says otherwise.
5. Report back.

Work from the directory given above. If something unexpected comes up mid-task, stop and ask. Do not guess.

### Test-driven development

Write the test first and watch it fail. **No production code without a failing test**, for features, fixes, refactors, and behavior changes alike.

1. **RED** — Write one minimal test for one behavior, against real code. Run it. Confirm it *fails*, and fails because the feature is missing rather than because of a typo. A test that passes immediately is testing existing behavior, so fix the test.
2. **GREEN** — Write the simplest code that passes. No extra features (YAGNI). Confirm the new test passes, every other test still passes, and the output is clean.
3. **REFACTOR** — Only once green: remove duplication, improve names, extract helpers. Keep the tests green and add no behavior.

Found a bug? Write a failing test that reproduces it before fixing it.

### Testing anti-patterns

Tests must verify real behavior, not mock behavior. Mocks isolate; they are not the thing under test.

| Anti-pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test the real component or unmock it |
| Test-only methods in production | Move them to test utilities |
| Mock without understanding | Understand the dependency, then mock minimally |
| Incomplete mocks | Mirror the real data structure completely |
| Tests as afterthought | Tests first |
| Over-complex mocks | Consider an integration test with real components |

Red flags: assertions on `*-mock` IDs, methods only called from tests, mock setup larger than the test logic, a test that fails when you remove a mock, or mocking "just to be safe".

### Code organization

Follow the file structure the plan defines. Give each file one clear responsibility. If a file grows past the plan's intent, stop and report it as DONE_WITH_CONCERNS rather than splitting it yourself. In existing code, follow established patterns and improve what you touch, but leave anything outside the task alone.

### When you are in over your head

Stop and escalate. Bad work is worse than no work, and escalating costs you nothing.

Escalate when the task needs an architectural decision with several valid answers, when you need to understand code beyond what you were given and cannot find clarity, when the task requires restructuring the plan did not anticipate, or when you have been reading file after file without gaining ground.

Report BLOCKED or NEEDS_CONTEXT, and say what you are stuck on, what you tried, and what help you need.

### Self-review before reporting

- **Completeness:** Did you implement everything in the spec? Any missed requirements or unhandled edge cases?
- **Quality:** Are the names accurate? Is the code clean and maintainable?
- **Discipline:** Did you avoid overbuilding? Did you follow the codebase's existing patterns?
- **Testing:** Do the tests verify behavior rather than mocks? Did you write each test first and watch it fail?

Fix what you find before reporting.

### Committing

After self-review, follow the commit instruction above.

- **No instruction, or "commit":** stage this task's changes and make one commit, matching the repo's recent style (`git log --oneline -10`).
- **"Don't commit":** leave the changes uncommitted.
- **A custom rule:** follow it.

Commit only this task's work. If you find unrelated changes, report them rather than sweeping them in. Never amend, rebase, force-push, or push. Make at most one commit.

### Report format

- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented, or attempted if blocked
- What you tested, and the results
- Files changed
- Self-review findings, if any
- Any issues or concerns

Use DONE_WITH_CONCERNS when the work is complete but you have doubts about correctness. Never silently produce work you are unsure about.
