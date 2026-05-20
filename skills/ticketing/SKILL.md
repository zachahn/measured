---
name: ticketing
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

Claude needs to write an excellent ticket. Claude will be given some information but will need to find or query for other information.

## Required: user is in the loop

This skill is a collaboration with the user, not a solo run. You MUST stop and wait for the user's reply at every step that uses `AskUserQuestion` and at the final confirmation. Do not infer answers, do not pick approaches on the user's behalf, do not advance steps on your own.

**Auto Mode does NOT override this.** Auto Mode lets you skip *clarifying* pauses where you'd otherwise check in out of caution. It does not authorize you to skip *required* user inputs. The questions in this skill are required inputs — a ticket the user didn't actually shape is the wrong ticket, no matter how plausible it looks.

If you catch yourself about to proceed past an `AskUserQuestion` step without a user message in between, stop. That is the bug this skill exists to prevent.

An excellent ticket:

- Describes the outcome in full detail
- Describes the constraints (performance targets, backward compatibility, accessibility)
- Suggests the approach only when context may live outside this ticket — a specific API contract, a known footgun, an architectural decision already made
- Leaves the implementation to the engineer
- Leaves nothing ambiguous

Too much implementation detail is a smell. It means either the ticket author doesn't trust the engineers, or it was written by someone who's already mentally solved it and is just transcribing their solution. This kills ownership and often produces worse outcomes — the engineer follows a prescribed solution that was written before they understood the problem.

Too little product context is the more common failure. Engineers end up making product decisions mid-sprint because no one wrote down why the feature matters or what the edge cases are. This leads to technically correct but wrong-feeling outcomes.

## Workflow

1. Explore the codebase. Understand the current behavior and how this new ticket might affect it.
2. Clarify unknowns with `AskUserQuestion`. **Wait for the user's reply** before continuing. Skip only if every requirement is already unambiguous from the user's message and the code — "I can guess what they probably want" is not unambiguous.
3. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs. **Wait for the user's reply** before continuing. Do not pick for them.
4. Draft and revise the ticket:
    - Draft: `measured-note --ticket --append "..."`.
    - Revise: `measured-note --ticket --edit --old ... --new ...`.
5. Self review the ticket
    - `measured-note --ticket --read`
    - Consistency: Do any sections contradict each other?
    - Ambiguity: Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
6. Once the ticket is in a good place, use `Agent(measured:ticketing-review)` to review it.
    - Resolve all problems with the ticket.
    - Escalate unknowns to the user via `AskUserQuestion` and **wait for the user's reply**.
    - Rerun the review if making any significant changes.
7. Confirm the ticket with the user via `AskUserQuestion`. **Wait for the user's reply.** Do not assume approval.
8. After final confirmation, update or create the ticket in the requested ticketing system.

## Usage: `measured-note`

usage: measured-note (--ticket)
                     (--read | --append [TEXT] |
                      --edit --old TEXT --new TEXT [--replace-all])

Per-Claude-session note scratchpad.

Note type:
  --ticket

Action:
  --read           Read entire note
  --append [TEXT]  Append text
  --edit           Related flags: --old, --new, --replace-all


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
