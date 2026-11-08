---
name: spec
description: Write a product spec in RFC 2119 format
disable-model-invocation: true
---

When the caller uses this skill, typically the user will care about the direction and its details. Interview the caller to determine all necessary behavior, then write the spec.

It's paramount that there are no inconsistencies, especially when editing existing specifications. When editing an existing specification, alert the caller of any inconsistencies; offer to fix them.

Do not use AskUserQuestion; ask questions one at a time as each answer may significantly change the direction of the spec.

# Template

```markdown
# Title of Spec

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 (RFC2119) (RFC8174) when, and only when, they appear in all capitals, as shown here.

## 1. Overview

...
```
