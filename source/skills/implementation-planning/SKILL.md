---
name: implementation-planning
description: Draft a thorough implementation plan for feature development or bugfix.
---

Claude needs to write a thorough implementation plan.

## Required: user is in the loop

This skill is a collaboration with the user, not a solo run. You MUST stop and wait for the user's reply at every step that uses `AskUserQuestion` and at the final presentation. Do not infer answers, do not pick approaches on the user's behalf, do not advance steps on your own.

**Auto Mode does NOT override this.** Auto Mode lets you skip *clarifying* pauses where you'd otherwise check in out of caution. It does not authorize you to skip *required* user inputs. The questions in this skill are required inputs — a plan the user didn't actually shape is the wrong plan, no matter how plausible it looks.

If you catch yourself about to proceed past an `AskUserQuestion` step without a user message in between, stop. That is the bug this skill exists to prevent.

An excellent implementation plan:

- Restates the goal in engineering terms
- Provides the architectural design and approach
- Lists all tasks with no gaps, keeping dependencies in mind
- Considers maintainability
- Avoids YAGNI
- Scopes exactly one working, testable change

## Scope Check

If the design covers multiple independent subsystems, it should have been broken into sub-projects during Phase 1. If it wasn't, stop and suggest decomposition — one plan per subsystem. Each plan should produce working, testable software on its own.

## Workflow

1. Explore the codebase. Understand the current behavior and how this new ticket might affect it.
2. Clarify unknowns with `AskUserQuestion`. **Wait for the user's reply** before continuing. Skip only if every requirement is already unambiguous from the user's message and the code — "I can guess what they probably want" is not unambiguous.
3. Use `AskUserQuestion` to propose 2+ approaches with tradeoffs. **Wait for the user's reply** before continuing. Do not pick for them.
    - Lead with your recommended approach and explain why
    - Cover: architecture, key libraries or patterns, how it integrates with existing code
4. Assess scope. Determine if this warrants multiple plans. If decomposition is needed, surface that to the user via `AskUserQuestion` and **wait for the user's reply** before continuing.
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
    - Escalate unknowns to the user via `AskUserQuestion` and **wait for the user's reply**.
    - Rerun the review if making any significant changes.
8. Present plan to the user and **wait for the user's reply** before any downstream skill begins implementation. Do not assume approval.

## Usage: `measured-plan`

<%= `/usr/bin/env python3 #{root.join("bin/measured-plan").to_s} --help` %>

## System design

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

## Task Structure

- Each appended task must work as its own, TDD-based commit.
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
