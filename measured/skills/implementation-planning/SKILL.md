---
name: implementation-planning
description: Draft a thorough implementation plan for feature development or bugfix.
disable-model-invocation: true
---

Claude needs to write a thorough implementation plan.

An excellent implementation plan:

- Restates the goal in engineering terms
- Provides the architectural design and approach
- Lists all tasks with no gaps, keeping dependencies in mind
- Considers maintainability
- Avoids YAGNI
- Scopes exactly one working, testable change

## Collaborate with the user

Claude can never know the user's intent without asking. Proactively understand the problem and consider the solution; but never infer answers, never pick on the user's behalf, and never advance phases on your own.

Claude must collaborate with the user to create the optimal solution. Always stop and wait for the user's reply.

"Auto Mode" does not override this. "Auto Mode" will try to stop Claude from breaking the user's computer. "Auto Mode" still means Claude must collaborate.


## Scope Check

If the design covers multiple independent subsystems, it should have been broken into sub-projects during Phase 1. If it wasn't, stop and suggest decomposition — one plan per subsystem. Each plan should produce working, testable software on its own.

## Workflow

1. Explore the codebase. Understand the current behavior and how this new ticket might affect it.
2. Clarify unknowns with `AskUserQuestion`.
3. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs.
    - Lead with your recommended approach and explain why
    - Cover: architecture, key libraries or patterns, how it integrates with existing code
4. Assess scope. Determine if this warrants multiple plans.
5. Expand chosen approach
    - Architecture and components
    - Data flow
    - Error handling
    - Testing approach
5. Draft and revise the plan:
    - Draft: `measured-plan --append "Task Title" "Task Body"`.
    - Revise: `measured-plan --edit "Task Title" --old ... --new ...`.
6. Self review the plan
    - `measured-plan --all`
    - Consistency: Do any sections contradict each other? Does the architecture match the feature descriptions?
    - Scope: Is this focused enough for a single implementation plan, or does it need decomposition?
    - Ambiguity: Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
7. Once the plan is in a good place, use `Agent(measured:implementation-planning-review)` to review it.
    - Resolve all problems with the ticket.
    - Escalate unknowns to the user.
    - Rerun the review if making any significant changes.
8. Present plan.

## Usage: `measured-plan`

usage: measured-plan (--add TITLE [TEXT] | --append TITLE [TEXT] |
                      --edit TITLE --old TEXT --new TEXT [--replace-all] |
                      --move TITLE (--before TITLE | --after TITLE) |
                      --remove TITLE | --read TITLE | --list | --all)

Per-Claude-session agenda of ordered markdown items.

Actions:
  --add TITLE [TEXT]      Create new item (body from TEXT or stdin)
  --append TITLE [TEXT]   Append to an item's body
  --edit TITLE            Edit body; requires --old and --new (optionally --replace-all)
  --move TITLE            Reorder; requires --before or --after
  --remove TITLE          Delete an item
  --read TITLE            Print one item's file
  --list                  Print titles in sort order
  --all                   Print every item's file


## System design

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

## Task Structure

- Each appended task must work as its own, TDD-based commit.
- Always use exact file paths
- Do not prefix task titles with numbers (e.g. `"1. Add parser"`, `"Task 2: ..."`). `measured-plan` orders tasks itself; numbering in the title duplicates that and goes stale on `--move`.
- Template below

---

# Task/Component Name

## Affected files

- Create: `exact/path/to/new.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test.py`

## Step 1: Write the failing test

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

## Step 2: Run test to verify it fails

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

## Step 3: Write minimal implementation

```python
def function(input):
    return expected
```

## Step 4: Run test to verify it passes

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

## Step 5: Commit

```bash
git add exact/path/to/new.py exact/path/to/existing.py tests/exact/path/to/test.py
git commit -m "Make specific change"
```
