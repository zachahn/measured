---
name: plan
description: Choose an approach with the user and break it into ordered, committable steps in PLAN.md.
disable-model-invocation: true
argument-hint: "[slug]"
---

Produce `PLAN.md`: the chosen approach plus an ordered list of steps, each small enough to implement, test, and commit in one sitting. The fork in the road — which approach — belongs to the user; the decomposition is your craft.

## Workspace

Notes live in `.weighed/<slug>/` at the repo root — one directory per effort, shared across sessions.

- Pick the slug with the user: short, kebab-case, named after the effort (e.g. `csv-export`). Resume an existing directory when one matches; list `.weighed/*/` when unsure.
- Before the first write, keep the directory out of git:
  `git check-ignore -q .weighed || echo '.weighed/' >> "$(git rev-parse --git-path info/exclude)"`
- These files are working notes for Claude. Never mention `.weighed`, the slug, step numbers, or this workflow in commit messages, code comments, branch names, or PR text.

## Steps

1. Read `SPEC.md` and `ORIENTATION.md`. If `SPEC.md` is missing, **GATE**: offer to run `/weighed:define` first, or to proceed treating the user's request as the spec.
2. Read the actual files the work will land in. Seams come from the code, not from imagination.
3. **GATE** — Propose two or more approaches with `AskUserQuestion`. Lead with your recommendation and say why. For each: how it integrates with existing code, its blast radius, and what it punts.
4. Write `PLAN.md`. Order steps by dependency; every step leaves the tree working and committable. When the change is hard, make the first steps refactoring that makes it easy, then make the easy change.

   ```markdown
   # Plan: <imperative title>

   ## Approach
   The chosen approach in prose: how it fits the existing architecture,
   what gets refactored first, and why this shape.

   ## Steps
   - [ ] **Imperative step title**
     - Change: what and where, with real file paths.
     - Done when: a condition someone else could check, ideally a test.
     - Out of scope: what this step must not touch.
   ```

5. Self-check coverage: every acceptance criterion in `SPEC.md` traces to a step, and no step exists without a criterion or the approach demanding it.
6. Fresh eyes: spawn the `weighed:doc-critic` agent on `PLAN.md` (tell it the path and that it is a plan). Fix what it finds yourself; bring findings that need the user to the next gate.
7. **GATE** — Confirm the shape with the user: the step titles, their order, and anything the critic surfaced. Cheap to re-slice now, expensive after the third commit.

## Escalation

The user invoked this skill to be consulted. That choice outranks any default to act autonomously.

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and put the question to the user with `AskUserQuestion`, even when you are confident of the answer.
- Between gates, work without interrupting. Verify what you can yourself; ask only what the code cannot answer.
- Subagents report to you; you escalate what matters to the user.
