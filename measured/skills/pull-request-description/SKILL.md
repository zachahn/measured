---
name: pull-request-description
description: Use whenever creating a request for a code review
disable-model-invocation: false
---

- Include a recommended order of which files to review first.
- For each file with medium-to-large nontrivial changes, provide a one-sentence overview of its behavior.

# Template

## Large PR (more than 3 files, or more than 200 LOC)

```markdown
### Recommended review order

The helper code does .... The main file does ....

- path/to/helper/file
- path/to/main/file
```
