---
name: ticketing-review
---

Review the ticket `measured-note --ticket --read`. We want to create an excellent ticket that provides enough context for an engineer to implement this task with no blockers.

An excellent ticket provides context but does not over-prescribe implementation details.

Pay particular attention to:

- Contradictions
- Clarity
- Consequences
- Missing sections, missing details


## Required sections

Ensure it has all of the required information.

- **Title of Feature:** This must be in imperative mood.
- **Problem / Why:** A few sentences on the problem being solved.
- **User Stories:** User stories in "Given, When, Then" format.
- **Acceptance Criteria:** Bullet list of observable, testable conditions.
- **Scope:** List of items in and out of scope.
- **Edge cases and Error states:** Empty states, failed API calls. What's likely, and how to resolve?
- **Technical and design context:** List of code areas, designs, etc that are a good starting point

## Calibration

Only flag issues that would cause real problems during implementation planning.

- Flag: A missing section, a contradiction, or a requirement so ambiguous it could be interpreted two different ways.
- Do not flag: Minor wording improvements, stylistic preferences, and "sections less detailed than others".

Approve unless there are serious gaps that would lead to a flawed execution.

## Output Format

---

# Plan Review

**Status:** Approved | Issues Found

**Issues (if any):**
- [Section X]: [specific issue] - [why it matters for planning]

**Recommendations (advisory, do not block approval):**
- [suggestions for improvement]

