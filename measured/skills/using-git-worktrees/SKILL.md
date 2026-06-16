---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees and verifies the worktree directory is gitignored
disable-model-invocation: true
---

# Using Git Worktrees

Git worktrees give each branch its own working directory while sharing one repository, so you can work without disturbing the current checkout.

## Steps

1. **Confirm the worktree directory is gitignored.** Run the bundled script:

   ```bash
   ./skills/using-git-worktrees/scripts/check-ignore
   ```

   If it reports "not ignored", add the directory to `.gitignore` and commit before continuing. This keeps worktree contents out of the repo.

2. **Create the worktree.** Call `EnterWorktree(name: "<branch-name>")`. The session's working directory switches to the new worktree.

3. **Run setup.** Read the repo's setup commands with `measured-config --get worktree-setup` and run what it prints.

   - If it prints nothing, no setup is configured. Ask the user what commands prepare a fresh checkout (install deps, build), then store them with `measured-config --set worktree-setup "<commands>"` so the next worktree skips this question. Run them.

4. **Verify a clean baseline.** Run the project's test command. If tests fail, report the failures and ask whether to proceed or investigate. If they pass, report ready.

5. **Report location.**

   ```
   Worktree ready at <full-path>
   Tests passing (<N> tests, 0 failures)
   Ready to implement <feature-name>
   ```

## Watch out

- After `EnterWorktree` (and after `ExitWorktree`) the working directory changes. When unsure which tree you're in, run `git rev-parse --show-toplevel`.
- Do not proceed past failing baseline tests without explicit permission — otherwise you can't tell new bugs from pre-existing ones.

## Integration

**Called by:**
- **implement** - REQUIRED before executing any tasks
- Any skill needing an isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work is complete
- **measured-config** - stores the `worktree-setup` commands this skill runs
