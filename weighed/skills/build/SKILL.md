---
name: build
description: Execute PLAN.md step by step in the main conversation — test, commit, and review as you go.
disable-model-invocation: true
argument-hint: "[slug]"
---

Execute the plan in this conversation. You implement; subagents only review. Never dispatch implementer subagents — they cost tokens, lose the user's words, and drift from the plan.

## Workspace

Notes live in `.weighed/<slug>/` at the repo root — one directory per effort, shared across sessions.

- Resume the directory that matches; list `.weighed/*/` when unsure.
- These files are working notes for Claude. Never mention `.weighed`, the slug, step numbers, or this workflow in commit messages, code comments, branch names, or PR text.

## Setup

1. Read `PLAN.md` and `SPEC.md`. If `PLAN.md` is missing, **GATE**: offer to run `/weighed:plan` first.
2. **GATE** when on `main`/`master`: ask before creating a branch or proceeding in place.
3. Run the test suite for a clean baseline. If it fails, **GATE**: report the failures and ask whether to proceed.
4. Mirror the steps into your session todo list for in-session tracking. The checkboxes in `PLAN.md` remain the cross-session record — keep both current.

## Per step

1. Re-read the step and the spec criteria it serves.
2. When "Done when" can be expressed as a test, write that test first and watch it fail for the right reason, then write the minimal code to pass. When it cannot, verify by running the code and say so in the journal.
3. Run the project's tests and fix failures before moving on; each step starts green.
4. Self-review the diff: names that say what things do, no leftover debris, edge cases from the spec handled. Leave every file you touch better than you found it.
5. Commit. Describe the change in the code's own vocabulary.
6. Tick the step's checkbox in `PLAN.md` and append one line to `JOURNAL.md`: what landed, plus any decision or surprise.

When reality disagrees with the plan: cosmetic drift (a rename, a moved file) goes in the journal; material drift (a step is wrong, missing, or mis-ordered) is a **GATE** — show the user the conflict and the options before rewriting the plan.

## Review

After the final step — and after every third step on longer plans — spawn the `weighed:change-reviewer` agent. Paste into its prompt: the steps covered, the relevant spec criteria, your summary of what you built, and the base and head SHAs. Fix Blocking and Important findings, then have it re-review. Record Minor findings in the journal. When you believe a finding is wrong, escalate to the user rather than arguing or silently ignoring it.

## Finish

1. Run the full test suite.
2. Check every acceptance criterion in `SPEC.md`. Report each one as met, with evidence, or as unmet — plainly, without hedging.
3. **GATE** — Present the options: merge locally, push and open a PR, or leave the branch for the user. Execute the choice.

## Escalation

The user invoked this skill to be consulted. That choice outranks any default to act autonomously.

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and put the question to the user with `AskUserQuestion`, even when you are confident of the answer.
- Between gates, work without interrupting. Verify what you can yourself; ask only what the code cannot answer.
- Subagents report to you; you escalate what matters to the user.
