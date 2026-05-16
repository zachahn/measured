---
name: ticketing
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

We need to write an excellent ticket. Claude will be given some information but will need to find or query for other information.

An excellent ticket:

- Describes the outcome in full detail
- Describes the constraints (performance targets, backward compatibility, accessibility)
- Suggests the approach only when context may live outside this ticket — a specific API contract, a known footgun, an architectural decision already made
- Leaves the implementation to the engineer

Too much implementation detail is a smell. It means either the ticket author doesn't trust the engineers, or it was written by someone who's already mentally solved it and is just transcribing their solution. This kills ownership and often produces worse outcomes — the engineer follows a prescribed solution that was written before they understood the problem.

Too little product context is the more common failure. Engineers end up making product decisions mid-sprint because no one wrote down why the feature matters or what the edge cases are. This leads to technically correct but wrong-feeling outcomes.

## Workflow

1. Explore the codebase. Understand the current behavior and how this ticket might affect it.
2. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs.
3. Clarify unknowns with `AskUserQuestion`.
4. Confirm the ticket with the user.
    - Draft: `measured-note --ticket --append "..."`.
    - Revise with `measured-note --ticket --edit --old ... --new ...`.
5. After final confirmation, Update or Create the ticket in the requested ticketing system.

## Usage: `measured-note`

usage: measured-note [-h] [--ticket-draft] [--ticket] [--read] [--edit]
                     [--append [TEXT]] [--old TEXT] [--new TEXT]
                     [--replace-all]

Per-Claude-session note scratchpad.

options:
  -h, --help       show this help message and exit

note type (exactly one required):
  --ticket-draft
  --ticket

action (exactly one required):
  --read
  --edit
  --append [TEXT]

edit arguments (only valid with --edit):
  --old TEXT
  --new TEXT
  --replace-all


## Output

### Required sections
- Problem / Why: One or two sentences on the user or business problem being solved. This is the most skipped and most valuable field. It lets engineers make good judgment calls when implementation surprises arise.
- Acceptance criteria: The contract between product and engineering. Bullet list of observable, testable conditions. "Given X, when Y, then Z."
- Scope: Explicitly call out what is and isn't included. This prevents well-intentioned scope creep.
- Edge cases & error states: What happens when things go wrong? Empty states, failed API calls, permission errors. These get forgotten until QA.

### Recommended sections
- Technical context (light, not prescriptive): Pointers to relevant code areas, APIs, or data models. Not "implement it this way" but "this touches the auth service, here's the relevant file."
- Design / mockups: Link if provided.
