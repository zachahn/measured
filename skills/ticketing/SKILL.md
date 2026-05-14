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

The ticket must include at least a bulleted list of Acceptance Criteria.

Ideally, include:

- Context and background
- Problem statement or user story
- Steps to reproduce (if a bug)
- Scope / out of scope
- Edge cases
- Design & technical references (full path to notable files)

## Usage: `measured-ticket`

usage: measured-ticket [-h] [--cache-step [TEXT]] [--list-steps]
                       [--read-step NAME] [--read-all-steps]
                       [--draft-ticket [TEXT]] [--get-ticket] [--edit-ticket]
                       [--force] [--old TEXT] [--new TEXT] [--replace-all]

Per-Claude-session ticket scratchpad.

options:
  -h, --help            show this help message and exit
  --cache-step [TEXT]
  --list-steps
  --read-step NAME
  --read-all-steps
  --draft-ticket [TEXT]
  --get-ticket
  --edit-ticket
  --force
  --old TEXT
  --new TEXT
  --replace-all


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
