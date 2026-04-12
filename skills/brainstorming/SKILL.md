---
name: brainstorming
description: "Only use this skill if explicitly asked. Two-phase design process: understand what to build, then plan how to build it."
---

## Overview

**Phase 1 — Understand the Request**:

Delegate to "brainstorm-request" Subagent.

Wait for the subagent to complete before starting Phase 2. Use its Phase 1 Summary as the input to Phase 2.

**Phase 2 — Implementation Plan**:

After entering Plan mode, use the updated request to create a thorough implementation plan.


## Anti-pattern: "This is too simple to need a design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.


## Phase 1 — Understand the request

Phase 1 is handled by a subagent.

```
Agent tool (brainstorm-request):
  description: "Understand user's request"
  prompt: |
    **User's original request:** [USER_REQUEST]
    **Project directory:** [PROJECT_DIR]
```

Wait for the subagent to complete before starting Phase 2. Use its Phase 1 Summary as the input to Phase 2.


## Phase 2 — Implementation Plan

Phase 2 answers **how** to build what Phase 1 defined.

First, enter Plan mode (see: EnterPlanMode, Plan subagent).

Next, use `TaskCreate` to create a task for each step below:

1. Explore project context
2. Ask clarifying questions
3. Propose 2-3 approaches
4. Expand chosen approach
5. Self-review the output


### Step 1: Explore project context

Read relevant files with an implementation focus. Look for:
- Existing patterns and conventions to follow
- Functions and utilities that can be reused — avoid proposing new code when suitable implementations exist
- Files that will need to change
- Test patterns and coverage approach

### Step 2: Ask clarifying questions

Use AskUserQuestion for anything the Phase 1 Summary left unresolved, or new questions that emerged from the implementation-focused exploration. Don't re-ask what Phase 1 already answered.

### Step 3: Propose 2-3 implementation approaches

Present 2-3 technical approaches with trade-offs.

- Lead with your recommended approach and explain why
- Cover: architecture, key libraries or patterns, how it integrates with existing code
- Keep it conversational — not yet a full design, just the options

**Understanding the idea:**

- Before going deep on one approach, assess scope: if the request covers multiple independent subsystems, flag this. Help the user decompose into sub-projects. Each sub-project gets its own plan.

### Step 4: Expand chosen approach

Once the user picks (or confirms yours), present the full design in sections scaled to their complexity. Cover:

- Architecture and components
- Data flow
- Error handling
- Testing approach

Ask after each section whether it looks right so far.

Write and update the Plan file.

Assume the engineer has zero context for the codebase and questionable taste. Document everything they need to know: which files to touch, code, testing, docs to check, how to test it. Give the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits. Assume a skilled developer who knows almost nothing about the toolset or problem domain and doesn't know good test design.

**Header:**

```markdown
# Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
```

#### Scope Check

If the design covers multiple independent subsystems, it should have been broken into sub-projects during Phase 1. If it wasn't, stop and suggest decomposition — one plan per subsystem. Each plan should produce working, testable software on its own.

#### File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

#### Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

#### Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

#### No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

#### Remember
- Exact file paths always
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits


## Plan Document Reviewer

After writing both sections of the plan document, dispatch a subagent to review it:

Use the Agent tool (general-purpose) with the prompt template in:
`skills/brainstorming/plan-document-reviewer-prompt.md`

Replace `[PLAN_FILE_PATH]` with the path to the Claude Code plan file.

Wait for the reviewer's response:
- **Issues Found:** Fix them inline in the plan file, then call ExitPlanMode.
- **Approved:** Call ExitPlanMode immediately.


## Key Principles

- **YAGNI ruthlessly** — Remove unnecessary features from all designs
- **Explore alternatives** — Always propose 2-3 approaches before settling
- **Incremental validation** — Present design, get approval before moving on

**Design for isolation and clarity:**
- Break the system into units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit: what does it do, how do you use it, what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are easier to reason about and more reliable to edit. When a file grows large, that's often a signal it's doing too much.

**Working in existing codebases:**
- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

### Step 5: Self-review the output

Ensure that the Plan file was written to. Look at the design with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix issues inline. No need to re-review — just fix and move on.
