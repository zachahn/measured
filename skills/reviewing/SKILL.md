---
name: reviewing
description: Use when the user explicitly asks to review a pull request, branch, or other code change — orchestrates a multi-agent code review and prints the result to the invoking user in the command line. User-invoked only; do not trigger on general "look at this code" or "review my changes" requests that don't reference a specific PR or branch.
---

# Reviewing a Pull Request

Provide a code review for the given input. The user will pass in a branch name, a GitHub PR URL/number, or similar reference to a code change.

First, use the skill `measured:using-git-worktrees` and use the `EnterWorktree` tool.

To do this, follow these steps precisely:

1. Make sure we are within a worktree.
2. Inside that worktree, fetch the branch under review (`git fetch origin <branch>`) and then `git reset --hard` the worktree to that branch so the working tree matches the change exactly. If the input is a GitHub PR, resolve it to the head branch before fetching.
3. Use a Haiku agent to view the change (something like `git diff origin/main...HEAD` in the worktree), and ask the agent to return a summary of the change.
4. Then, invoke these agents to independently code review the change:
   - Agent #1: Invoke the agent: `measured:reviewing-claude-compliance`. Pass the absolute path of the worktree directory as the argument.
   - Agent #2: Invoke the agent: `measured:reviewing-git-history`. Pass the absolute path of the worktree directory as the argument.
   - Agent #3: Invoke the agent: `measured:reviewing-file-comments`. Pass the absolute path of the worktree directory as the argument.
   - Agent #4: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
   - Agent #5: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
   - Agent #6: Invoke the agent: `measured:reviewing-changes`. Pass the absolute path of the worktree directory as the argument.
5. Aggregate, de-duplicate, and sort issues by priority.

Examples of false positives, for step 4:

- Pre-existing issues
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter, typechecker, or compiler would catch (eg. missing or incorrect imports, type errors, broken tests, formatting issues, pedantic style issues like newlines). No need to run these build steps yourself -- it is safe to assume that they will be run separately as part of CI.
- General code quality issues (eg. lack of test coverage, general security issues, poor documentation), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)
- Changes in functionality that are likely intentional or are directly related to the broader change
- Real issues, but on lines that the user did not modify in their pull request

Notes:

- Do not check build signal or attempt to build or typecheck the app. These will run separately, and are not relevant to your code review.
- Use `gh` to interact with Github (eg. to fetch a pull request's metadata or diff), rather than web fetch. Do not use `gh` to post comments on the pull request.
- Make a todo list first.
