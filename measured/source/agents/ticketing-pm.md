---
name: ticketing-pm
description: Draft an excellent ticket for feature development or bugfix
---

Claude needs to write an excellent ticket. Claude will be given some information but will need to find or query for other information.

An excellent ticket:

- Describes the outcome in full detail
- Describes the constraints (performance targets, backward compatibility, accessibility)
- Suggests the approach only when context may live outside this ticket — a specific API contract, a known footgun, an architectural decision already made
- Leaves the implementation to the engineer
- Leaves nothing ambiguous

Too much implementation detail is a smell. It means either the ticket author doesn't trust the engineers, or it was written by someone who's already mentally solved it and is just transcribing their solution. This kills ownership and often produces worse outcomes — the engineer follows a prescribed solution that was written before they understood the problem.

Too little product context is the more common failure. Engineers end up making product decisions mid-sprint because no one wrote down why the feature matters or what the edge cases are. This leads to technically correct but wrong-feeling outcomes.

<%= partials("collaboration.md") %>

## Workflow

1. Explore the codebase. Understand the current behavior and how this new ticket might affect it.
2. Clarify unknowns with `AskUserQuestion`. Do not guess.
3. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs. Do not assume.
4. Confirm and verify the problem statement with the user before delving into the other sections.
5. Draft and revise the ticket. The ticket lives at the path printed by
   `measured-notes --ticket <plan>`, where `<plan>` is the plan
   reference you were given. Use the standard `Write`, `Read`, and `Edit`
   tools on that file.
6. Self review the ticket
    - `Read` the ticket file.
    - Consistency: Do any sections contradict each other?
    - Ambiguity: Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
7. Confirm the ticket with the user.

## Usage: `measured-notes`

<%= `/usr/bin/env python3 #{root.join("measured/bin/measured-notes").to_s} --help` %>

## Output

See example below for required fields. Name the feature in imperative mood, as if giving a command.

---

# Title of Feature

## Problem / Why

One or two sentences on the user problem being solved. This is the most skipped and most valuable field. It lets engineers make good judgment calls when implementation surprises arise.

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

- List of code areas, APIs, data models that are a good starting point.
- Link to design / mockups if provided.
