---
name: define
description: Pin down what the user wants — problem, outcome, acceptance criteria — into SPEC.md.
disable-model-invocation: true
argument-hint: "[slug or request]"
---

Produce `SPEC.md`: a statement of what the user wants, precise enough that an engineer who never met the user could implement it. Interview the user in this conversation — never guess on their behalf, and never hand the interview to a subagent.

## Workspace

Notes live in `.weighed/<slug>/` at the repo root — one directory per effort, shared across sessions.

- Pick the slug with the user: short, kebab-case, named after the effort (e.g. `csv-export`). Resume an existing directory when one matches; list `.weighed/*/` when unsure.
- Before the first write, keep the directory out of git:
  `git check-ignore -q .weighed || echo '.weighed/' >> "$(git rev-parse --git-path info/exclude)"`
- These files are working notes for Claude. Never mention `.weighed`, the slug, step numbers, or this workflow in commit messages, code comments, branch names, or PR text.

## Steps

1. Read `ORIENTATION.md` if present. If absent, explore just enough to ask informed questions — leave the full survey to `/weighed:orient`.
2. Interview the user with `AskUserQuestion`, biggest unknown first:
   - **GATE** — Confirm the problem: who hurts, when, and why solving it matters. Settle this before any solution talk.
   - **GATE** — Confirm the outcome: what observably changes when the work is done. When the request supports more than one reading, offer each as an option.
   - Then the edges: error states, empty states, scope boundaries. Batch related questions. Skip anything the code already answers.
3. Define terms. List every word specific to this effort that two engineers could read two ways — domain jargon, internal names, acronyms. One line each. Use these terms verbatim everywhere after.
4. Write `SPEC.md`:

   ```markdown
   # <Imperative title naming the change>

   ## Problem
   Who hurts, when, and why solving it matters. One or two sentences.

   ## Outcome
   What observably changes when this is done.

   ## Definitions
   - **Term:** one-line meaning in this effort's context.

   ## Acceptance criteria
   Observable, testable conditions. Someone other than the author can check each one.

   ## Out of scope
   Adjacent things a reasonable engineer might do here but must not.

   ## Edge cases and error states
   Empty states, failures, permission errors — decided now, not at review.

   ## Open questions
   Must end empty, or each entry explicitly deferred by the user.
   ```

5. Fresh eyes: spawn the `weighed:doc-critic` agent on `SPEC.md` (tell it the path and that it is a spec). Fix what it finds yourself; bring findings that need the user to the next gate.
6. **GATE** — Walk the user through the spec: outcome, acceptance criteria, and anything still open or deferred. Revise until they confirm it.

## Escalation

The user invoked this skill to be consulted. That choice outranks any default to act autonomously.

- Raise the biggest unknown first — a wrong guess at the top costs the most to unwind.
- Stop at every **GATE** and use `AskUserQuestion`. Never advance past a gate on inference, and never answer a gate question on the user's behalf.
- Between gates, work without interrupting. Verify what you can yourself; ask only what the code cannot answer.
- Subagents never address the user. They report to you; you escalate what matters.
