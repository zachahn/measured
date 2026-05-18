---
name: brainstorm-specification
---

You are helping to understand a user's request before implementation planning begins. Your job is to figure out **what** to build — not how.

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

Ask 1-4 targeted questions. Only ask what you need to understand the request — don't ask for things you can infer from the code.

Good questions to consider:

- What problem does this solve for the user?
- Are there constraints (performance, compatibility, existing interfaces)?
- What does success look like?
- Is there existing code this should integrate with or replace?

Skip this step if you already have enough to proceed with confidence.

## Step 2: Propose 2-3 approaches

Present 2-3 different interpretations or scope options for **what** to build. Focus on problem framing and scope — not implementation details.

For each approach:

- What it is (1-2 sentences)
- Key trade-offs
- When you'd choose it

Lead with your recommended approach and explain why.

## Step 3: Expand chosen approach

Once the user picks an approach (or confirms yours), expand it into a full description:

- Goals and non-goals
- Key requirements
- Scope boundaries
- Any constraints or known risks

## Step 4: Self-review the output

Before presenting, check your work:

- Are there any ambiguous requirements that could be interpreted two ways? Pick one and make it explicit.
- Are there any scope gaps — things the user clearly expects but you haven't addressed?
- Are there any contradictions?
- Is there anything missing that would leave Phase 2 without enough to plan?
- Are all file paths full file paths?
- Are there any open questions?

Fix issues inline.

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

Fix all of the issues that the subagents find.

## Step 7: Present finalized plan

Call `ExitPlanMode` for the user to review.
