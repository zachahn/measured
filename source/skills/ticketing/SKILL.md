---
name: ticketing
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

We need to draft an excellent ticket. Claude will be given some information but will need to find or query for other information.

## Workflow

1. Explore the codebase. Understand the current behavior and how this ticket might affect it.
2. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs.
2. Clarify unknowns with `AskUserQuestion`.
3. Cache findings as you go: `measured-ticket --cache-step "..."`.
5. Draft: `measured-ticket --draft-ticket "..."`. Review steps with `--read-all-steps` first.
6. Revise with `--edit-ticket --old ... --new ...`.
7. Confirm the ticket with the user.
8. After final confirmation, Update or Create the ticket in the requested ticketing system.

## Usage: `measured-ticket`

<%= `/usr/bin/env python3 #{root.join("bin/measured-ticket").to_s} --help` %>

## Output

### Required sections
- Acceptance Criteria (bulleted, testable)

### Recommended sections
- Context / background
- Problem statement or user story
- Steps to reproduce (bugs)
- Scope / out of scope
- Edge cases
- Design & technical references (full file paths)
