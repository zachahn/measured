---
name: reviewing-claude-compliance
description: Only use when directed to
model: sonnet
permissionMode: default
effort: high
tools: Read, Grep, Glob, Bash(git diff origin/main...HEAD)
---

Within the provided directory, audit the changes to make sure they comply with the CLAUDE.md. Note that CLAUDE.md is guidance for Claude as it writes code, so not all instructions will be applicable during code review.

<%= partials("reviewing_helpers.md") %>
