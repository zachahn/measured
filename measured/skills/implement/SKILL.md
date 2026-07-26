---
name: implement
description: Use when executing implementation plans with independent tasks in the current session
disable-model-invocation: true
---

Execute a plan one task at a time. You read the tasks, implement each one yourself, and gate it through two reviews before moving to the next.

You work from a **plan dir** — the directory holding the plan's files, which persists across sessions.

- If you were given a plan dir path or a `TICKET.md` path, use that dir.
- Otherwise, run `measured-notes` (no arguments) to print this repo's state dir, then list its `YYYY-MM-DD-slug` plan dirs and pick the one the user means.

Build each file's path by joining its filename to the plan dir:

- List the dir's `TASK-N.md` files (Glob/`ls`) to enumerate the tasks; their numbers run in dependency order.
- A task's path is `<plan-dir>/TASK-N.md`.
- The architecture plan is `<plan-dir>/ARCHITECTURE.md`.

Read `ARCHITECTURE.md` in full before starting, so you know the shape of the work. Read each task closely when you reach it.

## GATE: where should this work happen?

Before starting any task, settle where the work runs. Read the stored preference with `measured-config --get work-location`. The stored value is the source of truth: follow it even if the prompt suggests otherwise. To change the behavior, change the setting.

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

## GATE: commit each task?

You commit each task's work yourself after self-review. Resolve the commit instruction **before starting the first task**, then apply it to every task.

1. Read it with `measured-config --get commit-behavior`. The stored value is the source of truth: follow it even if the prompt suggests otherwise. To change the behavior, change the setting.
2. **If it prints nothing (unset/null):** you cannot proceed without a selection. Use `AskUserQuestion` to ask whether to commit each task after review. Store the answer with `measured-config --set commit-behavior after-every-turn` (or `on-user-request`) so later tasks skip the question.
3. **If `after-every-turn`:** commit each task's work once its reviews pass.
4. **If `on-user-request`:** leave the work uncommitted.
5. **If any other value:** follow it verbatim, so the user's rule (e.g. "commit only after the last task") governs whether and how you commit.

Also read `measured-config --get commit-location`, `--get commit-style`, `--get commit-scope`, `--get commit-body`, `--get commit-signoff`, and `--get commit-attribution`. Follow every value that prints, so these commits match the rest of the repo. Skip any that print nothing.

Commit only the current task's work. If you find unrelated changes, report them rather than sweeping them in. Never amend, rebase, force-push, or push.

### Verify the rule was followed

After each task's reviews pass, check the outcome against the commit instruction. Run `git status --porcelain` and `git log --oneline -1` in the working directory:

- **Commit expected:** the latest commit covers this task's work and the working tree is clean. If the tree still holds this task's changes, commit them now.
- **No commit expected:** this task's changes sit uncommitted and no new commit was made.
- **Custom rule:** check the outcome against the rule (e.g. "commit only after the last task" means no commit until the final task). If it diverges, correct it before moving on.

## Run one task at a time

Work through the tasks in dependency order. Finish each one, including both reviews, before starting the next.

1. **Read the task.** Open `<plan-dir>/TASK-N.md` and the section of `ARCHITECTURE.md` it implements. Raise questions about the requirements, the approach, or anything unclear **before** you start writing code.
2. **Implement exactly what the task specifies**, test-first (see Test-Driven Development below). Build nothing the task did not ask for.
3. **Self-review** (see below). Fix what you find before moving to review.
4. **Review for spec compliance first.** Spawn a teammate using the subagent: `measured:spec-reviewer`. Give it the task requirements and a report of what you built. Fix what it finds, then re-review. Repeat until ✅.
5. **Review code quality second**, only after spec compliance is ✅. Spawn a teammate using the subagent: `measured:code-quality-reviewer`. Give it your report, the task reference, the base and head SHAs, and a task summary. Fix what it finds, then re-review. Repeat until approved.
6. **Verify the commit rule** (per "GATE: commit each task?" above).
7. Move to the next task only when both reviews are clear and the commit rule held.

After the last task, spawn `measured:code-quality-reviewer` once more across the whole change to confirm the plan is delivered and ready to merge.

## Test-Driven Development

Always write the test first, and always watch it fail. Write minimal code to pass. If you didn't watch the test fail, you don't know it tests the right thing.

**No production code without a failing test first.** This holds for new features, bug fixes, refactoring, and behavior changes.

The cycle:

1. **RED** — Write one minimal test for one behavior, with a clear name, against real code. Run it. Confirm it *fails* (not errors) and fails because the feature is missing, not because of a typo. A test that passes immediately tests existing behavior, so fix the test.
2. **GREEN** — Write the simplest code that passes. No extra features, no improving code beyond the test (YAGNI). Run it. Confirm the new test passes, all other tests still pass, and output is clean.
3. **REFACTOR** — Only once green: remove duplication, improve names, extract helpers. Keep tests green. Add no behavior.

Then repeat for the next behavior. Found a bug? Write a failing test that reproduces it before fixing, so the test proves the fix and prevents regression.

## Testing anti-patterns

Tests must verify real behavior, not mock behavior. Mocks isolate; they are not the thing under test.

| Anti-pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test the real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand the dependency first, then mock minimally |
| Incomplete mocks | Mirror the real API completely |
| Tests as afterthought | Tests first |
| Over-complex mocks | Consider an integration test with real components |

Red flags: assertions on `*-mock` IDs, methods only called in test files, mock setup larger than the test logic, a test that fails when you remove a mock, or mocking "just to be safe."

## Self-review before each review gate

Review your own work with fresh eyes before handing it to a reviewer:

- **Completeness:** Did you implement everything in the spec? Any missed requirements or unhandled edge cases?
- **Quality:** Are names accurate? Is the code clean and maintainable?
- **Discipline:** Did you avoid overbuilding (YAGNI)? Did you follow the codebase's existing patterns?
- **Testing:** Do the tests verify behavior rather than mocks? Did you write each test first and watch it fail?

Follow the file structure the plan defines. Each file gets one clear responsibility. If a file grows past the plan's intent, stop and raise it rather than reorganizing on your own. In existing code, improve what you touch the way a good developer would, but leave anything outside the task alone.

## When you're in over your head

Stop and escalate to the user when the task needs an architectural decision with several valid answers, when it requires restructuring the plan did not anticipate, or when you have been reading file after file without gaining ground. Bad work is worse than no work.

Bad assumptions and miscommunication are expensive. Self-research, but escalate all questions and concerns to the user.
