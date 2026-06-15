---
name: plan
description: Turn a story into an architecture plan and a set of implementation-ready tasks.
disable-model-invocation: true
---

You are given an input — usually a story from `measured:story`, sometimes a looser description. Your job is to understand it, design an architecture, and break that architecture into well-scoped tasks.

## What a good plan does

- Restates the product goal in engineering terms.
- Follows the patterns the codebase already uses.
- Refactors to make the change easy, then makes the easy change.
- Stays reasonably DRY, considers WET, avoids YAGNI.
- Leaves no vestigial systems and punts no problems.

## What good tasks do

- **Slice along seams, not layers.** Each task ships a thin vertical slice that leaves the system working and mergeable — not "all the models, then all the controllers."
- **Run in dependency order.** A reader starts at task 1 and goes; every dependency points backward.
- **Right-size the work.** Roughly a half-day to two days each. Split a task whose acceptance criteria span unrelated concerns; merge two that always touch the same lines.
- **Name what NOT to do.** One "Out of Scope" line written up front is the cheapest scope-creep prevention.

## Escalate, don't infer

Bad assumptions and miscommunication are expensive. Research what you can yourself, but never infer an answer or pick on the user's behalf. Bring every open question and unexpected find to the user with `AskUserQuestion`.

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and put the question to the user with `AskUserQuestion`, even when you are confident. Do not proceed on silence.
- Between gates, work without interrupting. Verify what the code can answer; ask only what it cannot.

## Find the plan

The plan is a directory that persists across sessions. The story already created one.

1. If you were given a plan dir path or a `TICKET.md` path, use that dir. Read `<plan-dir>/TICKET.md` — it is the input you are planning from.
2. If you have no plan dir (the input is a loose description, not a story), run `measured-notes --new-plan-dir "<short description>"`. It prints the dir's absolute path, e.g. `.../2026-06-13-add-rate-limiting`. Write the input you were given into `<plan-dir>/TICKET.md` so the rest of the work has a source of truth.

Build every other file's path by joining its filename to the plan dir: `<plan-dir>/ARCHITECTURE.md`, `<plan-dir>/TASK-1.md`, and so on.

## Phase 1 — Architecture

The architecture plan lives at `<plan-dir>/ARCHITECTURE.md`.

1. Spawn an `Explore` subagent to research the codebase and return conclusions with file references (not file contents): the current behavior this change touches, the patterns and modules an implementer would build on, and where the work will land.
2. **GATE:** Confirm the engineering goal — restate the story in engineering terms and check that restatement with the user before any solution talk.
3. **GATE:** Use `AskUserQuestion` to propose two or more approaches with their tradeoffs. Lead with your recommendation and say why. Cover architecture, key libraries or patterns, and how it integrates with existing code.
4. Draft the architecture into `<plan-dir>/ARCHITECTURE.md` using the template below. Write it as you settle each section.
5. Self-review: `Read` the file back. Do any sections contradict each other? Could any requirement be read two ways? If so, pick one and make it explicit.
6. Spawn the `measured:plan-architecture-reviewer` subagent. Give it the plan dir path and nothing else — no summary of the conversation. Fix what it finds; take anything you can't resolve to the user.
7. **GATE:** Present the plan with `AskUserQuestion` and iterate until the user confirms it.

## Phase 2 — Task breakdown

Each task is its own file at `<plan-dir>/TASK-N.md`, numbered from 1 in dependency order.

1. Re-read `<plan-dir>/ARCHITECTURE.md`. It is the source of truth; the tasks decompose it. Every task traces back to a part of the plan, and the tasks together deliver it with no gaps.
2. **GATE:** Confirm the overall shape with the user — titles, the dependency order — before fleshing out every section. Re-slicing an outline is cheap; rewriting seven full tasks is not.
3. Write each task into its own `<plan-dir>/TASK-N.md` using the template below. List the dir's `TASK-N.md` files to track what you've created. Don't reuse a filename.
4. Self-review: `Read` every task back.
    - **Ordering:** Does every dependency point backward? Can someone start at task 1 and proceed?
    - **Sizing:** Is any task secretly three? Is any too thin to stand alone?
    - **Testability:** Could two engineers disagree about whether a task's acceptance criteria are met? Tighten it.
    - **Coverage:** Do the tasks together deliver the architecture plan? What falls in the gaps?
5. Spawn the `measured:implementation-ticketing-review` subagent. Give it the plan dir path and nothing else — no summary of the conversation. Fix what it finds; take anything you can't resolve to the user.

## Architecture template

```markdown
# Title of Implementation Plan

## Problem Statement

What needs to change, written for an engineer who wasn't in the meetings. One paragraph max.

## Approach

### System changes

Walk through which system components will change and how. Of equal importance, mention what should not change.

Consider:

- What does the system component expect? (Inputs, state)
- What does the system component guarantee? (Outputs, state)
- What does the system component maintain? (Invariants, state)
```

## Task template

Title in imperative mood. Use the file's number so the title matches its filename (`Task 3`). Omit a field only when it doesn't apply — say so rather than leaving it blank.

```markdown
# Task N: Imperative, specific title

Action-oriented — "Add rate limiting to /api/auth endpoints", not "Rate limiting".

## Context / Background

One to three sentences: why this task exists and which section of `<plan-dir>/ARCHITECTURE.md` it implements. The implementer shouldn't need to go digging.

## Acceptance Criteria

The most important section. Testable conditions, not vague goals — a checklist or Given/When/Then. This defines done.

- Given <context>, when <action>, then <observable result>.
- [ ] <objectively verifiable item>

## Technical Guidance

Pointers, not a spec. Relevant files, services, or patterns; known gotchas; a preferred approach if one exists — but leave room for the implementer to decide.

## Out of Scope

Adjacent things someone might reasonably do here but shouldn't.

## Dependencies

Other tasks that must land first, or that this one blocks. External APIs, infra, or team dependencies. Write "None" if it stands alone.

## Definition of Done / Testing Notes

How to test it — unit, integration, manual — and edge cases worth covering. Call out anything operational: a migration, a feature flag, a rollback plan.
```
