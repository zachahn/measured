---
name: reviewing-git-history
description: Only use when directed to.
model: sonnet
permissionMode: default
effort: high
tools: Read, Grep, Glob, Bash(git diff origin/main...HEAD)
---

Within the provided directory, read the git blame and history of the code modified, and identify any bugs in light of that historical context.

<%= partials("reviewing_helpers.md") %>
