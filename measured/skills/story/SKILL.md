---
name: story
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

## What makes a ticket excellent

- Describes the outcome and its constraints (performance targets, backward compatibility, accessibility) in full detail.
- Leaves nothing ambiguous.
- Leaves the implementation to the engineer. Suggest an approach only when the context lives outside the ticket — a specific API contract, a known footgun, an architectural decision already made.

Too much implementation detail kills the engineer's ownership and transcribes a solution written before anyone understood the problem. Too little product context forces the engineer to make product decisions mid-sprint. Aim between the two.

Never infer an answer or pick on the user's behalf. Bring every open question and unexpected find to the user with `AskUserQuestion`.

## How to interview

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and put the question to the user with `AskUserQuestion`, even when you are confident of the answer. Do not proceed on silence.
- Between gates, work without interrupting. Verify what you can yourself; ask only what the code cannot answer.
- When the request supports more than one reading, offer each as an option with its consequences.
- Subagents report to you; you escalate what matters to the user.

## Set up the plan

The ticket lives in a **plan** — a directory that persists across sessions.

1. Run `measured-notes --new-plan-dir "<short description>"` to create one. It prints the plan dir's absolute path, e.g. `.../2026-06-13-add-rate-limiting`.
2. The ticket file is `<plan-dir>/TICKET.md` — join that filename to the plan dir path. Use `Read`, `Write`, and `Edit` on that file.

## Draft in three stages

The template's sections build on each other: a wrong problem statement corrupts everything after it. Draft one stage at a time, write each into the ticket file as it firms up, and get the user's explicit confirmation before starting the next. Do not proceed on silence.

**Stage 1 — Foundation: Title, Problem / Why, Definitions.**

1. Spawn an `Explore` subagent to research the codebase and return conclusions with file references (not file contents): the current behavior this ticket would change, the terms and jargon the code already uses, and the code areas, APIs, and data models an implementer would start from. Keep the last group — it becomes Stage 3.
2. **GATE:** Confirm the problem first — who hurts, when, and why solving it matters. Settle this with the user before any solution talk.
3. Draft the title (imperative mood), the problem statement, and the definitions. Define every term specific to this feature — domain jargon, internal names, acronyms, any word an outside engineer could read two ways — each as a term plus a one-line meaning in this ticket's context.
4. Write the stage into the ticket file.
5. **GATE:** Present it with `AskUserQuestion` and wait for confirmation.

**Stage 2 — Behavior: User Stories, Acceptance Criteria, Scope.**

1. Draft the three sections. Reuse the confirmed definitions verbatim.
2. **GATE:** Where a real choice exists — competing behaviors, scope boundaries, tradeoffs — use `AskUserQuestion` to propose two or more options with their consequences.
3. Write the stage into the ticket file.

**Stage 3 — Details: Edge cases and Error states, Technical and design context.**

1. Draft both sections from the confirmed foundation and the Stage 1 exploration, and write them into the ticket file.
2. If a gap surfaces — an error path the exploration missed — spawn another targeted `Explore` rather than reading the code yourself.

## Review before sign-off

The finished ticket must stand alone: an engineer who never saw this conversation implements from the page. You cannot test that yourself — everything the user told you is in your context, so a gap on the page still reads as covered.

1. Spawn the `story-review` subagent. Give it the ticket's path (`<plan-dir>/TICKET.md`) and nothing else — no summary of the conversation.
2. Fix what it finds. Take anything you cannot resolve to the user.
3. Present the full ticket and iterate until the user is satisfied.

## Ticket template

ALWAYS use this exact structure:

```markdown
# Title of Feature

## Problem / Why

One or two sentences on the user problem being solved. This is the most skipped and most valuable section. It lets engineers make good judgment calls when implementation surprises arise.

## Definitions

- **Term:** One-sentence meaning in this ticket's context. Reuse these terms verbatim throughout the ticket.

## User Stories

- Given some background context
    - When a scenario happens
        - Then expect a result
        - Then expect this other result
    - When another scenario happens
        - Then expect this specific result.

## Acceptance Criteria

- Bullet list of observable, testable conditions.

## Scope

- List of items in and out of scope.

## Edge cases and Error states

- What happens when things go wrong? Empty states, failed API calls, permission errors. These get forgotten until QA.

## Technical and design context

- Link to design / mockups if provided.
- Up to three full filepaths that might be a useful starting point when starting to implement.
```
