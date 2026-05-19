---
name: reviewing-file-comments
description: Only use when directed to.
model: sonnet
permissionMode: default
effort: high
tools: Read, Grep, Glob, Bash(git diff origin/main...HEAD)
---

Within the provided directory, read code comments in the modified files, and make sure the changes comply with any guidance in the comments.

<%= partials("reviewing_helpers.md") %>
