#!/usr/bin/env python3
"""SessionStart hook: inject the "Writing Clearly" guidance into context.

This was formerly the `writing-clearly` skill. A skill only applies when it is
invoked, so the guidance was easy to forget. As a SessionStart hook it is
injected automatically at the top of every session and re-injected after a
compaction (source `compact`), a resume, or a `/clear` — the moments when prior
context is dropped or summarized away and the guidance would otherwise be lost.

The guidance prose lives in `writing-clearly.md` next to this file so it can be
edited as plain markdown. SessionStart hooks add to Claude's context by
returning `hookSpecificOutput.additionalContext`; we read the markdown and emit
it there, ignoring stdin since the source/session payload does not change what
we inject.
"""

import json
from pathlib import Path

GUIDANCE_PATH = Path(__file__).resolve().parent / "writing-clearly.md"


def main():
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": GUIDANCE_PATH.read_text(encoding="utf-8"),
        }
    }))


if __name__ == "__main__":
    main()
