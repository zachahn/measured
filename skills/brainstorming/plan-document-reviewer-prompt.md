# Plan Document Reviewer Prompt Template

Use this template when dispatching a plan document reviewer subagent.

**Purpose:** Verify the plan is complete, internally consistent, and ready for implementation.

**Dispatch after:** The complete plan document is written into the Claude Code plan file.

```
Task tool (general-purpose):
  description: "Review plan document"
  prompt: |
    You are a plan document reviewer. Verify this plan is complete and ready for implementation.

    **Plan to review:** [PLAN_FILE_PATH]

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | TODOs, placeholders, incomplete tasks, missing steps |
    | Goal/Architecture Alignment | Tasks implement what the plan header's Goal and Architecture declare; no unexplained scope creep |
    | Clarity | Requirements ambiguous enough to cause someone to build the wrong thing |
    | Task Decomposition | Tasks have clear boundaries, steps are actionable, each step is 2-5 minutes |
    | No Placeholders | "TBD", "TODO", "implement later", "add appropriate error handling", "similar to Task N", steps without code when code is needed |
    | Buildability | Could an engineer follow this plan without getting stuck? Every file path exact, every command runnable, every type consistent across tasks? |
    | YAGNI | Unrequested features, over-engineering, speculative abstractions |

    ## Calibration

    **Only flag issues that would cause real problems during implementation.**
    An implementer building the wrong thing or getting stuck is an issue.
    Minor wording, stylistic preferences, and "nice to have" suggestions are not.

    Approve unless there are serious gaps — missing requirements from the goal,
    contradictory steps, placeholder content, or tasks so vague they can't be acted on.

    ## Output Format

    ## Plan Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Task X, Step Y]: [specific issue] - [why it matters for implementation]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer returns:** Status, Issues (if any), Recommendations
