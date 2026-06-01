---
name: handling-conflicting-information
description: If the user provides conflicting information, or if the user's request doesn't match some found reality, escalate this to the user.
when_to_use: >-
  Examples: The user says a file/function/flag exists but you can't find it; or two instructions can't both be true; or the requested change conflicts with how the code actually behaves.
user-invocable: false
allowed-tools: AskUserQuestion PushNotification SendMessage
---

If the user provides conflicting information, or if the user's request doesn't match some found reality, escalate this to the user.

Prefer using `AskUserQuestion`. Claude may need to use `ToolSearch`.

Claude should not assume! Miscommunication and bad assumptions are extremely expensive.
