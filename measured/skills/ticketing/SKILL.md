---
name: ticketing
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

Two constraints shape how this skill divides the work:

- Subagents cannot ask the user questions. The dialogue — clarifying the problem, proposing options, confirming each stage — must happen in this conversation.
- The main conversation's context is precious. Push the context-heavy work — codebase research, the fresh-eyes review — into subagents that return conclusions, not file dumps.

So: draft the ticket and talk to the user yourself; delegate reading. Bad assumptions and miscommunication are expensive — research freely through subagents, but bring every open question and concern to the user with `AskUserQuestion`. Never infer an answer or pick on the user's behalf.

## What makes a ticket excellent

- Describes the outcome in full detail
- Describes the constraints (performance targets, backward compatibility, accessibility)
- Suggests the approach only when context lives outside this ticket — a specific API contract, a known footgun, an architectural decision already made
- Leaves the implementation to the engineer
- Leaves nothing ambiguous

Too much implementation detail is a smell. It means either the ticket author doesn't trust the engineers, or someone already mentally solved the problem and is transcribing their solution. This kills ownership and often produces worse outcomes — the engineer follows a prescribed solution written before they understood the problem.

Too little product context is the more common failure. Engineers end up making product decisions mid-sprint because no one wrote down why the feature matters or what the edge cases are. This leads to technically correct but wrong-feeling outcomes.

## Where the ticket lives

The ticket lives in a **plan** — a directory that persists across sessions:

- `measured-notes --plan-new` allocates one and prints its directory, e.g. `.../PLAN-0007`. The plan's reference is its number (`7`).
- `measured-notes --ticket <plan>` prints the ticket's path. Use the standard `Read`, `Write`, and `Edit` tools on that file.

Those two commands are all this skill needs; `measured-notes --help` lists the rest.

## Draft in stages, confirm the foundation

The template's sections build on each other: a wrong problem statement or a fuzzy definition quietly corrupts everything written after it. So draft in three stages, write each stage into the ticket file as it firms up, and get the user's explicit confirmation before building on it. Confirming early is cheap; rewriting a finished ticket because the problem statement was wrong is not.

**Stage 1 — Foundation: Title, Problem / Why, Definitions.**

Spawn an `Explore` subagent to research the codebase: the current behavior this ticket would change, the terms and jargon the code already uses, and the code areas, APIs, and data models a future implementer would start from (collect these now — they become Stage 3's technical-context section). Have it return conclusions with file references, not file contents.

From its findings, draft the title (imperative mood, as if giving a command), the problem statement, and the definitions. Define every term specific to this feature — domain jargon, internal names, acronyms, any word an outside engineer could read two ways — each as a term plus a one-line meaning in this ticket's context. Ask the user about anything ambiguous rather than guessing.

Present this stage with `AskUserQuestion` and wait for confirmation. Do not proceed on silence.

**Stage 2 — Behavior: User Stories, Acceptance Criteria, Scope.**

Where a real choice exists — competing behaviors, scope boundaries, tradeoffs — use `AskUserQuestion` to propose two or more options with their consequences. Reuse the confirmed definitions verbatim throughout. Confirm this stage with the user before moving on.

**Stage 3 — Details: Edge cases and Error states, Technical and design context.**

These follow from the confirmed foundation and the Stage 1 exploration, so draft them directly and fold them into the ticket. If a gap surfaces — an error path the exploration didn't cover — spawn another targeted `Explore` rather than reading the code yourself.

## Review before sign-off

The finished ticket must stand alone: an engineer who never saw this conversation will implement from the page. You cannot test that property yourself — everything the user told you is in your context, so a gap on the page still reads as covered. Spawn the `ticketing-review` subagent instead.

Give it the ticket's path (from `measured-notes --ticket <plan>`) and nothing else — no summary of the conversation. It checks for contradictions, ambiguity, inconsistent or undefined terms, missing sections, and whether an engineer could plan the work with no blockers, then returns findings rather than edits.

Fix what it finds; take anything you cannot resolve to the user. Then present the full ticket and iterate until the user is satisfied.

## Ticket template

ALWAYS use this exact structure:

```markdown
# Title of Feature

## Problem / Why

One or two sentences on the user problem being solved. This is the most
skipped and most valuable section. It lets engineers make good judgment
calls when implementation surprises arise.

## Definitions

- **Term:** One-sentence meaning in this ticket's context. Reuse these
  terms verbatim throughout the ticket.

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

- What happens when things go wrong? Empty states, failed API calls,
  permission errors. These get forgotten until QA.

## Technical and design context

- List of code areas, APIs, data models that are a good starting point.
- Link to design / mockups if provided.
```
