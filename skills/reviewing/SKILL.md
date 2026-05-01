---
name: reviewing
description: Use when the user explicitly asks to review a pull request, branch, or other code change — orchestrates a multi-agent code review and prints the result to the invoking user in the command line. User-invoked only; do not trigger on general "look at this code" or "review my changes" requests that don't reference a specific PR or branch.
---

# Reviewing a Pull Request

Provide a code review for the given input. The user will pass in a branch name, a GitHub PR URL/number, or similar reference to a code change.

First, use the skill `measured:using-git-worktrees` and use the `EnterWorktree` tool.

To do this, follow these steps precisely:

1. Make sure we are within a worktree.
2. Inside that worktree, fetch the branch under review (`git fetch origin <branch>`) and then `git reset --hard <branch>` the worktree to that branch so the working tree matches the change exactly.
3. Sometimes, the change is simple enough where a thorough review would not useful. To determine this, invoke the agent: `measured:reviewing-useful`. Pass the absolute path of the worktree directory as the argument, and also pass in any instruction from the prompt that would affect this decision (prefer a verbatim reproduction of the prompt; avoid summarizing or rewording). If the result is to stop, stop.
4. Invoke the agent: `measured:reviewing-summary`. Pass the absolute path of the worktree directory as the argument.
5. Then, invoke these agents to independently code review the change:
   - Agent #1: Invoke the agent: `measured:reviewing-claude-compliance`. Pass the absolute path of the worktree directory as the argument.
   - Agent #2: Invoke the agent: `measured:reviewing-git-history`. Pass the absolute path of the worktree directory as the argument.
   - Agent #3: Invoke the agent: `measured:reviewing-file-comments`. Pass the absolute path of the worktree directory as the argument.
   - Agent #4: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
   - Agent #5: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
   - Agent #6: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
6. For each low-confidence, high impact issue, verify the issue by invoking the agent: `measured:reviewing-detail`. Pass in the absolute path of the worktree as the argument. Pass in the details of a single potential issue.
7. Use `ExitWorktree(discard_changes: true)`. Prefer removing the directory as we have made no changes. Avoid confirming; it is easy to rebuild this worktree. Verify that all todo tasks were taken.
8. Aggregate, de-duplicate, and sort issues by priority. Avoid listing pre-existing issues unless if it is extremely high impact. Verify that all todo tasks were taken.

Notes:

- Do not check build signal or attempt to build or typecheck the app. These will run separately, and are not relevant to your code review.
- Use `gh` to interact with Github (eg. to fetch a pull request's metadata or diff), rather than web fetch. Do not use `gh` to post comments on the pull request.
- Make a todo list first.

Format:

---
# Title

Summary of changes.

## Issues

### HIGH / MEDIUM / LOW / NIT

**Summary of issue**
File: full/relative/path/to/file
Long-form description of issue

## Conclusions

Note the complexity of the change. Note if this is an easy approve.
