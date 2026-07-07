#!/usr/bin/env python3
"""Stop hook: catch compressed noun-pile writing in Claude's own messages.

The `writing-clearly` SessionStart hook injects the full rules. This hook
enforces them per turn. When Claude finishes a turn, this reads the transcript,
pulls the text of Claude's last message, and runs heuristics for the failure
mode Zach hates: stacked abstract nouns with no verb ("one runtime mechanism,
two authoring forms"), nominalized verbs ("compilation failure results in
deployment cessation"), and paragraphs stuffed with abstract nouns. One abstract
noun is fine; a pile of them is the tell.

On a hit it prints `hookSpecificOutput.additionalContext` naming only the rules
the message broke. Each offense quotes the exact bad substring and states the
one rule it violated, in the form `You said "...". You must NEVER ...`. Nothing
else rides along — no full rulebook, no `<guidance>` wrapper. That keeps the
injected block short and pointed at the actual mistake. False positives are
acceptable; the goal is to never let a noun-pile slip through, so the heuristics
err toward flagging.

The Stop hook payload arrives on stdin as JSON with `transcript_path` (a JSONL
file, one event per line). We ignore `stop_hook_active` intentionally: this hook
only adds context, it never blocks, so it cannot loop.
"""

import json
import re
import sys
from pathlib import Path

# Abstract nouns that carry no picture on their own. One is fine — real writing
# uses these words. A paragraph stuffed with them is the tell, so we never flag
# a single use. We count bare occurrences across the whole turn and flag only
# when the density crosses the limit.
ABSTRACT_NOUNS = (
    r"mechanism|component|form|approach|solution|resolution|paradigm|framework|"
    r"architecture|abstraction|layer|construct|pattern|strategy|methodology|"
    r"capability|functionality|infrastructure|implementation|integration|"
    r"orchestration|configuration|representation|consideration|dimension|"
    r"aspect|facet|element|entity|artifact|primitive|surface|vector|modality|"
    r"envelope|boundary|sugar|handle|sink|trace|semantics|invariant"
)
ABSTRACT_NOUN = re.compile(r"\b(" + ABSTRACT_NOUNS + r")\b", re.IGNORECASE)
ABSTRACT_DENSITY_LIMIT = 4

# Nominalized verbs: "-tion/-ment/-ance/-ence" nouns doing the work a plain
# verb should do. Two or more clustered together is a noun-pile.
NOMINALIZATION = re.compile(
    r"\b\w{4,}(tion|ment|ance|ence|ancy|ency|ality|ization|isation)\b",
    re.IGNORECASE,
)

# The signature noun-pile slogan: "one X, two Y" / "N adjective-noun,
# M adjective-noun" with no verb between the halves.
NOUN_PILE_SLOGAN = re.compile(
    r"\b(one|two|three|a single|single)\s+\w+(\s+\w+)?\s*,\s*"
    r"(one|two|three|a single|single|\w+)\s+\w+(\s+\w+)?\b",
    re.IGNORECASE,
)

# "X of Y of Z": three-plus stacked "of" prepositional phrases signal a pile.
OF_STACK = re.compile(
    r"\b\w+\s+of\s+\w+\s+of\s+\w+\b", re.IGNORECASE
)

# Em-dash and semicolon. We detect these but never name them in the guidance,
# so Claude gets no clue to route around the check. An em-dash joining clauses
# and a semicolon are both strong "an LLM wrote this" tells. Also catch a
# spaced hyphen (" - ") used as a stand-in dash.
EM_DASH = re.compile(r"—|\s-\s")
SEMICOLON = re.compile(r";")

# Passive voice with a named agent: "is/are/was/were/been <participle> ... by".
# Catches "every call is mediated by the engine". Name the actor, use a verb.
PASSIVE_BY = re.compile(
    r"\b(is|are|was|were|been|be)\s+\w+(ed|en)\b[^.!?]*\bby\b",
    re.IGNORECASE,
)


def last_assistant_text(transcript_path):
    """Return the text of the final assistant message, or '' if none."""
    path = Path(transcript_path)
    if not path.exists():
        return ""
    text = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        blocks = [b.get("text", "") for b in content
                  if isinstance(b, dict) and b.get("type") == "text"]
        joined = "".join(blocks).strip()
        if joined:
            text = joined  # keep overwriting; last non-empty one wins
    return text


def _offense(bad, rule):
    """Format one offense: quote the bad substring, state the rule it broke."""
    return f'You said "{_clip(bad)}". You must NEVER {rule}.'


def find_offenses(text):
    """Return a list of offense lines. Empty means the writing is clean.

    Each line quotes the exact bad substring and states the one rule it broke,
    in the form `You said "...". You must NEVER ...`.
    """
    offenses = []

    slogan = NOUN_PILE_SLOGAN.search(text)
    if slogan:
        offenses.append(_offense(
            slogan.group(0),
            "stack abstract nouns into a slogan. Give the sentence a subject, "
            "a verb, and an object, and make a concrete actor do the acting",
        ))

    of_stack = OF_STACK.search(text)
    if of_stack:
        offenses.append(_offense(
            of_stack.group(0),
            "stack prepositional phrases into a pile. Name the thing that acts "
            "and give it a plain verb",
        ))

    # One abstract noun is fine. A turn stuffed with them is the tell. Count
    # bare occurrences and flag past the density limit.
    abstract = ABSTRACT_NOUN.findall(text)
    if len(abstract) >= ABSTRACT_DENSITY_LIMIT:
        sample = ", ".join(dict.fromkeys(w.lower() for w in abstract))
        offenses.append(_offense(
            sample,
            "pack a paragraph with abstract nouns. Use concrete nouns the "
            'reader can picture. Write "the parser", not "the mechanism"',
        ))

    passive = PASSIVE_BY.search(text)
    if passive:
        offenses.append(_offense(
            passive.group(0).strip(),
            "write passive voice. Name the actor, then the verb. Write "
            '"the engine logs every call", not "every call is logged by the '
            'engine"',
        ))

    # A cluster of nominalizations in one sentence is the smell. Flag when a
    # single sentence carries two or more. Reuse the same split to catch
    # comma-overloaded sentences (three-plus structural commas = a clause pile).
    nom_flagged = False
    comma_flagged = False
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        stripped = sentence.strip()
        if not nom_flagged and len(NOMINALIZATION.findall(sentence)) >= 2:
            offenses.append(_offense(
                stripped,
                "pile up nominalizations. Turn them back into verbs. Write "
                '"the compiler rejects the file, so the deploy stops", not '
                '"compilation failure results in deployment cessation"',
            ))
            nom_flagged = True
        if not comma_flagged and stripped.count(",") >= 3:
            offenses.append(_offense(
                stripped,
                "cram many clauses into one sentence. Write one idea per "
                "sentence. Split it into short full sentences",
            ))
            comma_flagged = True
        if nom_flagged and comma_flagged:
            break

    # Detect em-dash and semicolon, but report them with generic wording. The
    # rule text never names this punctuation, so the offense must not either —
    # else it hands Claude a rule to game.
    if EM_DASH.search(text) or SEMICOLON.search(text):
        offenses.append(
            "You wrote with choppy punctuation. You must NEVER chop a "
            "sentence apart. Write short, full sentences instead."
        )

    return offenses


def _clip(text, limit=120):
    """Shorten an excerpt for the flagged-offenses list."""
    text = text.strip()
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return

    text = last_assistant_text(transcript_path)
    if not text:
        return

    offenses = find_offenses(text)
    if not offenses:
        return

    # Name only the rules this message broke. Each offense quotes the bad
    # substring and states its rule. No full rulebook rides along.
    context = "A writing check flagged your last message.\n" + "\n".join(
        f"- {o}" for o in offenses
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
