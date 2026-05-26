---
name: ticketing-beta
description: Draft an excellent ticket for feature development or bugfix
disable-model-invocation: true
---

Create an agent team:

1. Spawn a teammate using the sub-agent: `measured:ticketing-pm`
2. Spawn a teammate using the sub-agent: `measured:ticketing-review`
3. One must review the ticket as an experienced engineer.
    - `measured-note --ticket --read`
    - Verify that the ticket is implementable; that there is no ambiguity.

All sub-agents can and should ask the user for clarity.
