---
name: brainstorm
description: "Two-phase design process: understand what to build, then plan how to build it."
disable-model-invocation: true
---

## Overview

Two-phase design process:

- **Phase 1 — Understand the User Request:** Delegates to the `brainstorm-specification` subagent. Returns a Phase 1 Summary including the plan file path.
- **Phase 2 — Build the Implementation Plan:** Delegates to the `build-implementation-plan` subagent using the plan file path from Phase 1.

Each phase runs in its own subagent for clean context isolation.


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
