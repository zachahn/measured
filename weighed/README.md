# weighed

A staged development workflow for Claude Code. Single-threaded, file-backed, and built on the plugin format with no build step: edit `skills/` and `agents/` directly.

## Stages

Each stage is a slash command and stands alone. Run one, or run them in sequence.

| Command | Question it answers | Output |
|---|---|---|
| `/weighed:orient` | What does the code do today? | `ORIENTATION.md` |
| `/weighed:define` | What does the user want? | `SPEC.md` |
| `/weighed:plan` | How do we get there? | `PLAN.md` |
| `/weighed:build` | — executes the plan | commits + `JOURNAL.md` |
| `/weighed:one-shot` | all four, gates intact | all of the above |

Notes live in `.weighed/<slug>/` at the repo root, excluded from git via `.git/info/exclude`. No ticket numbers, no CLI, no database — plain markdown that any session can resume.

## Principles

- **Escalate early.** The biggest unknown surfaces first. Every stage stops at named gates and asks the user with `AskUserQuestion`; gates outrank any default to act autonomously.
- **One thread.** The main agent explores, interviews, plans, and implements in the conversation the user can see. Subagents are limited to read-only exploration and two reviewers (`doc-critic`, `change-reviewer`) that report back instead of talking to the user.
- **Nothing leaks.** Working notes never appear in commit messages, code comments, or PR text.
- **Leave it better.** Refactor to make the change easy, then make the easy change; every touched file ends better than it started.
