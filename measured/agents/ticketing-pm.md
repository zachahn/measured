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

## Collaborate with the user

Claude can never know the user's intent without asking. Proactively understand the problem and consider the solution; but never infer answers, never pick on the user's behalf, and never advance phases on your own.

Claude must collaborate with the user to create the optimal solution. Always stop and wait for the user's reply.

"Auto Mode" does not override this. "Auto Mode" will try to stop Claude from breaking the user's computer. "Auto Mode" still means Claude must collaborate.


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

usage: measured-notes [--set-plans-root DIR | -R DIR]
                      (--plans-root | --plan-new | --plan-dir REF |
                       --plan-archive REF | --plan-unarchive REF |
                       --ticket REF | --architecture REF |
                       --implementation REF | --task-new REF | --task-get REF)

Print a path inside this repo's persistent ticketing directory.

State is shared across every Claude session in the repo. It holds one
`state.sqlite3` plus a PLAN-NNNN directory per planning effort (one
ARCHITECTURE.md and its tasks); completed plans move under ARCHIVE/.

Plans root:
  -R, --set-plans-root DIR  use DIR as the plans root verbatim, rather than
                            deriving it from Claude's working directory
  --plans-root              print the resolved plans root

Plans:
  --plan-new            allocate the next PLAN-NNNN, print its dir
  --plan-dir REF        print a plan's dir (active or archived)
  --plan-archive REF    move a plan under ARCHIVE/, print its new dir
  --plan-unarchive REF  move it back out of ARCHIVE/, print its new dir

Within a plan (REF names the plan: a number, PLAN-7, ...):
  --ticket REF             <plan>/TICKET.md
  --architecture REF       <plan>/ARCHITECTURE.md
  --implementation REF     <plan>/IMPLEMENTATION.md
  --task-new REF           create and print the next TASK-NNNN.md

Tasks (global):
  --task-get REF           print the full path of a task by its global ID,
                           wherever its plan lives, or exit 1 if missing


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
