---
name: orient
description: Map the current state of the code relevant to a request, before specifying or planning. Writes ORIENTATION.md.
disable-model-invocation: true
argument-hint: "[slug or request]"
---

Build an accurate picture of the code as it is today, scoped to the user's request. The output is `ORIENTATION.md` — the ground truth that `/weighed:define` and `/weighed:plan` build on. Work in this conversation; spawn subagents only for read-only exploration.

## Workspace

Notes live in `.weighed/<slug>/` at the repo root — one directory per effort, shared across sessions.

- Pick the slug with the user: short, kebab-case, named after the effort (e.g. `csv-export`). Resume an existing directory when one matches; list `.weighed/*/` when unsure.
- Before the first write, keep the directory out of git:
  `git check-ignore -q .weighed || echo '.weighed/' >> "$(git rev-parse --git-path info/exclude)"`
- These files are working notes for Claude. Never mention `.weighed`, the slug, step numbers, or this workflow in commit messages, code comments, branch names, or PR text.

## Steps

1. Restate the request in one sentence. If you cannot, that is your biggest open question — raise it with the user now.
2. Explore the code the request touches. Read the load-bearing files yourself. For broad sweeps — many files, naming conventions, "where does X happen" — dispatch the built-in `Explore` subagent and keep only its conclusions.
3. Verify every claim the request makes about the code (file X exists, flag Y controls Z). Record each mismatch as a surprise; the user decides at the gate which version stands.
4. Write `ORIENTATION.md`:

   ```markdown
   # Orientation: <effort>

   ## Request
   One sentence restating what the user asked for.

   ## Current behavior
   What the system does today, with key file paths.

   ## How it works
   The flow a change would ride through, end to end.

   ## Constraints and patterns
   Conventions, invariants, and test setup the work must respect.

   ## Surprises
   Mismatches between the request and the code, and anything else unexpected.

   ## Open questions
   Ordered by blast radius — the question whose answer changes the most comes first.
   ```

5. **GATE** — Summarize for the user: current behavior, surprises, and the open questions in order. Put the top questions to the user with `AskUserQuestion`. Fold the answers back into the file.

## Escalation

The user invoked this skill to be consulted. That choice outranks any default to act autonomously.

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and put the question to the user with `AskUserQuestion`, even when you are confident of the answer.
- Between gates, work without interrupting. Verify what you can yourself; ask only what the code cannot answer.
- Subagents report to you; you escalate what matters to the user.
