---
name: spec
description: Write a product spec in RFC 2119 format
disable-model-invocation: true
---

When the caller uses this skill, typically the user will care about the direction and its details. Interview the caller to determine all necessary behavior, then write the spec.

It's paramount that there are no inconsistencies, especially when editing existing specifications. When editing an existing specification, alert the caller of any inconsistencies; offer to fix them.

# Interview

Treat the interview as a conversation, not a questionnaire. Each answer may significantly change the direction of the spec, so do not rush to the next question.

1. Ask one question per message. Do not use AskUserQuestion.
2. Read the caller's reply and check whether it contains a question, a doubt, or a request for your opinion.
   1. If it does, the open question is still unanswered, even if the reply also states a position. Respond to what the caller asked. Then stop and wait for the caller. Do not ask the next question.
   2. If it does not, continue to step 3.
3. Check whether the reply fully answers the open question.
   1. If it is partial or ambiguous, ask one follow-up about that same question.
   2. If it is a clear answer with nothing unresolved, confirm your understanding in one sentence and ask the next question.
4. Repeat steps 2 and 3 until every necessary behavior is decided. Then write the spec.

# Template

```markdown
# Title of Spec

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 (RFC2119) (RFC8174) when, and only when, they appear in all capitals, as shown here.

## 1. Overview

...
```
