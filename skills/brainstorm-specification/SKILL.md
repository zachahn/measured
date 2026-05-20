---
name: brainstorm-specification
---

You are helping to understand a user's request before implementation planning begins. Your job is to figure out **what** to build — not how.

## Required: user is in the loop

This skill exists because the user's input is the input. You MUST stop and wait for the user's reply at every checkpoint marked **Wait for user** below. Do not infer answers, do not pick approaches on the user's behalf, do not advance steps on your own.

**Auto Mode does NOT override this.** Auto Mode lets you skip *clarifying* pauses where you'd otherwise check in out of caution. It does not authorize you to skip *required* user inputs. The checkpoints in this skill are required inputs — a spec the user didn't actually shape is the wrong spec, no matter how plausible it looks.

If you catch yourself about to proceed past a **Wait for user** checkpoint without a user message in between, stop. That is the bug this skill exists to prevent.

## Setup

First, `EnterPlanMode` to enter Plan mode.

Use `TaskCreate` to create a task for each step below:

1. Ask clarifying questions
2. Propose 2-3 approaches
3. Expand chosen approach
4. Write specification to plan
5. Self-review the output
6. Review specification
7. Present plan

By the time you `ExitPlanMode`, all tasks must be completed.

## Step 1: Ask clarifying questions

Ask 1-4 targeted questions via `AskUserQuestion`. Only ask what you need to understand the request — don't ask for things you can infer from the code.

Good questions to consider:

- What problem does this solve for the user?
- Are there constraints (performance, compatibility, existing interfaces)?
- What does success look like?
- Is there existing code this should integrate with or replace?

You may skip this step only if every requirement is already unambiguous from the user's message and the code. "I can guess what they probably want" is not unambiguous — ask.

**Wait for user.** Do not proceed to Step 2 until the user has answered.

## Step 2: Propose 2-3 approaches

Present 2-3 different interpretations or scope options via `AskUserQuestion`. Focus on problem framing and scope — not implementation details.

For each approach:

- What it is (1-2 sentences)
- Key trade-offs
- When you'd choose it

Lead with your recommended approach and explain why.

**Wait for user.** Do not proceed to Step 3 until the user has picked an approach (or explicitly confirmed yours). Do not pick for them.

## Step 3: Expand chosen approach

Once the user picks an approach, expand it into a full description:

- Goals and non-goals
- Key requirements
- Scope boundaries
- Any constraints or known risks

If expanding the approach surfaces a new ambiguity or decision point that materially shapes scope, use `AskUserQuestion` and **Wait for user** before continuing.

## Step 4: Self-review the output

Before presenting, check your work:

- Are there any ambiguous requirements that could be interpreted two ways? Pick one and make it explicit.
- Are there any scope gaps — things the user clearly expects but you haven't addressed?
- Are there any contradictions?
- Is there anything missing that would leave Phase 2 without enough to plan?
- Are all file paths full file paths?
- Are there any open questions?

Fix issues inline. If a question can only be resolved by the user, ask via `AskUserQuestion` and **Wait for user**.

## Step 5: Write specification to plan

Enter plan mode using the `EnterPlanMode` tool. Write the approved specification into the plan file under a **User Specification** section. The plan file is the Claude Code plan for this session.

Use this structure:

```markdown
# User Specification: [Feature Name]

**Goal:** [One sentence — what this builds and why]

**Approach:** [Name of the chosen approach]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Non-goals
- [What's explicitly out of scope]

## Key Decisions
- [Decision 1 and rationale]
- [Decision 2 and rationale]

## Constraints
- [Any known constraints]

## Notable Files
- [Any notable files with vital context for implementation plan]
```

## Step 6: Review specification

Dispatch the `review-specification` subagent to verify the spec is complete and ready for planning:

```
Agent tool (review-specification):
  description: "Review specification for completeness"
  prompt: |
    **Spec file:** [PLAN_FILE_PATH]
```

Fix all of the issues that the subagents find. If a fix requires a user decision, use `AskUserQuestion` and **Wait for user**.

## Step 7: Present finalized plan

Call `ExitPlanMode` for the user to review. **Wait for user** approval before any downstream skill begins implementation.
