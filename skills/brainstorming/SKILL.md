---
name: brainstorming
description: Two-phase design process: understand what to build, then plan how to build it.
disable-model-invocation: true
---

## Overview

Two-phase design process:

- **Phase 1 — Understand the Request:** Delegates to the `brainstorm-specification` subagent. Returns a Phase 1 Summary including the plan file path.
- **Phase 2 — Build the Implementation Plan:** Delegates to the `build-implementation-plan` subagent using the plan file path from Phase 1.

Each phase runs in its own subagent for clean context isolation.


## Anti-pattern: "This is too simple to need a design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.


## Phase 1 — Understand the request

```
Agent tool (brainstorm-specification):
  description: "Understand user's request"
  prompt: |
    **User's original request:** [USER_REQUEST]
    **Project directory:** [PROJECT_DIR]
```

Wait for the subagent to complete. Extract the **Plan file path** from its Phase 1 Summary — you will pass it to Phase 2.


## Phase 2 — Build the implementation plan

```
Agent tool (build-implementation-plan):
  description: "Build implementation plan"
  prompt: |
    **Plan file path:** [PLAN_FILE_PATH from Phase 1 Summary]
    **Project directory:** [PROJECT_DIR]
```

Wait for the subagent to complete.
