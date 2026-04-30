---
name: helpers-reviewing
disable-model-invocation: true
user-invocable: false
---

- The path that is provided via the prompt is the worktree directory to work in. Avoid reaching outside of this worktree as the contents of the main project are unpredictable.
- You can run `git diff origin/main...HEAD` to list the changes introduced by this branch
- You will need to score the impact of the issue. Explanation of impact score:
  - NIT: Non-behavioral. Style, naming, readability, small-scale duplication, or maintainability observations that a senior engineer would not block on. Avoid reporting on these types of errors.
  - LOW: Minor behavioral issue. A real bug or correctness gap, but on a rare edge case with limited blast radius. Worth flagging but not a merge blocker.
  - MEDIUM: Real issue worth fixing. Behavior is incorrect in a plausible case, error handling is weak, or the change makes future work meaningfully harder. The PR shouldn't merge without addressing it, but the impact is contained.
  - HIGH: Serious issue. Likely to break functionality in normal use, regress a feature, leak PII into logs, miss authorization scoping, ship a non-backward-compatible migration, cause data loss, or expose a security vulnerability. Must be fixed before merging.
- You will need to score the confidence of the issue. Explanation of confidence scores:
  - 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
  - 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
  - 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
  - 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
  - 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.

Format each issue like this:

> **Summary of issue**
> File: full/relative/path/to/file
> Long-form description of issue
> Impact: --
> Confidence Score: --
