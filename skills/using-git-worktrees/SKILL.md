---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees and verifies the worktree directory is gitignored
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Creation Steps

### 1. Verify Worktree Directory Is Ignored

Run the bundled script to confirm the worktree directory is gitignored:

```bash
./skills/using-git-worktrees/scripts/check-ignore
```

**If not ignored:** Add the directory to `.gitignore` and commit before proceeding. Prevents accidentally tracking worktree contents.

### 2. Create Worktree

```
EnterWorktree(name: "<branch-name>")
```

### 3. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Examples - use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| Starting isolated work | Run `check-ignore` then call `EnterWorktree` |
| Worktree directory not ignored | Add to `.gitignore` + commit |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes

### Assuming directory location

- **Problem:** After `EnterWorktree`, the session's working directory changes. Running commands as if you're still in the original repo (or vice versa after `ExitWorktree`) lands edits, tests, or git operations in the wrong tree
- **Fix:** Confirm with `pwd` or `git rev-parse --show-toplevel` when in doubt, especially right after entering or exiting a worktree

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

### Hardcoding setup commands

- **Problem:** Breaks on projects using different tools
- **Fix:** Auto-detect from project files (package.json, etc.)

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Run check-ignore - .claude/worktrees ignored]
[EnterWorktree(name: "auth")]
[Run npm install]
[Run npm test - 47 passing]

Worktree ready at .claude/worktrees/auth
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

## Red Flags

**Never:**
- Create a worktree without running `check-ignore` first
- Skip baseline test verification
- Proceed with failing tests without asking

**Always:**
- Run `check-ignore` before creating the worktree
- Use `EnterWorktree` to create the worktree
- Auto-detect and run project setup
- Verify clean test baseline

## Integration

**Called by:**
- **building** (Phase 4) - REQUIRED when design is approved and implementation follows
- **implementing-with-subagents** - REQUIRED before executing any tasks
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
