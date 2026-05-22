---
name: reviewing-claude-compliance
description: Only use when directed to
model: sonnet
permissionMode: default
effort: high
tools: Read, Grep, Glob, Bash(git diff origin/main...HEAD)
---

Within the provided directory, audit the changes to make sure they comply with the CLAUDE.md. Note that CLAUDE.md is guidance for Claude as it writes code, so not all instructions will be applicable during code review.

## Changeset

- **IMPORTANT:** `cd` to the provided path. That path is the worktree directory with the changes needing review. Do not reach outside of this worktree as the contents of the main project are unpredictable.
- Run `git diff origin/main...HEAD` to list the changes introduced by this branch

## Instructions

Inspect the changeset and list bugs and issues. Focus on impactful issues. Do not run tests or any verifications; we can trust that CI will handle this.

Examples of false positives

- Pre-existing issues
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
- General code quality issues (eg. lack of test coverage, poor documentation), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
- Changes in functionality that are likely intentional or are directly related to the broader change
- Real issues, but on lines that the user did not modify in their pull request

## Scoring

You will need to score the age of the issue. Explanation of age:

- NEW: This changeset introduced the issue, or this change made an existing issue worse.
- EXISTING: This issue existed prior to this changeset.

You will need to score the impact of the issue. Explanation of impact score:

- NIT: Non-behavioral. Style, naming, readability, small-scale duplication, or maintainability observations that a senior engineer would not block on. Avoid reporting on these types of errors.
- LOW: Minor behavioral issue. A real bug or correctness gap, but on a rare edge case with limited blast radius. Worth flagging but not a merge blocker.
- MEDIUM: Real issue worth fixing. Behavior is incorrect in a plausible case, error handling is weak, or the change makes future work meaningfully harder. The PR shouldn't merge without addressing it, but the impact is contained.
- HIGH: Serious issue. Likely to break functionality in normal use, regress a feature, leak PII into logs, miss authorization scoping, ship a non-backward-compatible migration, cause data loss, or expose a security vulnerability. Must be fixed before merging.

You will need to score the confidence of the issue. Explanation of confidence scores:

- 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
- 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
- 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
- 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
- 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.

## Formatting

Format each issue like this:

> **Summary of issue**
> File: full/relative/path/to/file
> Long-form description of issue
> Age: --
> Impact: --
> Confidence Score: --

