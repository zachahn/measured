---
name: ticketing-review
---

Review the ticket. `Read` it from the path printed by `measured-notes --ticket <project>`, where `<project>` is the project reference you were given. We want to create an excellent ticket that provides enough context for an engineer to implement this task with no blockers.

An excellent ticket provides context but does not over-prescribe implementation details.

<%= partials("reviewing_attention.md") %>

## Required sections

Ensure it has all of the required information.

- **Title of Feature:** This must be in imperative mood.
- **Problem / Why:** A few sentences on the problem being solved.
- **User Stories:** User stories in "Given, When, Then" format.
- **Acceptance Criteria:** Bullet list of observable, testable conditions.
- **Scope:** List of items in and out of scope.
- **Edge cases and Error states:** Empty states, failed API calls. What's likely, and how to resolve?
- **Technical and design context:** List of code areas, designs, etc that are a good starting point

<%= partials("review_plan_cohesion.md") %>
