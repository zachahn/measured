---
name: reviewing-useful
model: haiku
permissionMode: default
effort: high
tools: Bash, Read
skills:
- helpers-reviewing
---

Determine if the changes need to be reviewed or not. If the prompt does not provide any guidance, consider:

- Are the changes understandable from a simple skim?
- Is there a risk of a catastrophic failure introduced by this change?

---

Return either:

- REVIEW
- SKIP
