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
5. Draft and revise the plan. The implementation plan lives at the path printed
   by `measured-notes --implementation`. Use the standard `Write`, `Read`,
   and `Edit` tools on that file.
6. Self review the plan
    - `Read` the implementation plan.
    - Consistency: Do any sections contradict each other? Does the architecture match the feature descriptions?
    - Scope: Is this focused enough for a single implementation plan, or does it need decomposition?
    - Ambiguity: Could any requirement be interpreted two different ways? If so, pick one and make it explicit.
7. Once the plan is in a good place, use `Agent(measured:implementation-planning-review)` to review it.
    - Resolve all problems with the ticket.
    - Escalate unknowns to the user.
    - Rerun the review if making any significant changes.
8. Present plan.

## Usage: `measured-notes`

usage: measured-notes (--root-dir | --project-dir | --session-dir | --ticket |
                       --architecture | --implementation | --task-new |
                       --task-list | --task-get REF)

Print a path inside the per-Claude-session state directory.

Debugging (each prints a directory, superseding any target):
  --root-dir        the state root (holds every project's session dirs)
  --project-dir     this project's dir (holds every session dir for the repo)
  --session-dir     this session's dir (where the targets below live)

Single-file target (exactly one, unless a debugging flag is given):
  --ticket          <session>/TICKET.md
  --architecture    <session>/ARCHITECTURE.md
  --implementation  <session>/IMPLEMENTATION.md

Task series:
  --task-new        create and print the next <session>/TASK-NNN.md
  --task-list       print the basename of every TASK-NNN.md, in order
  --task-get REF    print the full path of a task (REF: 123, TASK-123,
                    or TASK-123.md), or exit 1 if it doesn't exist


## System design

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

## Task Structure

- Each task must work as its own, TDD-based commit.
- Always use exact file paths
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
