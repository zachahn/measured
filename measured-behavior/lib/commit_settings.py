"""The commit settings and the reminder rendered from them.

Six per-repo settings describe how a repo wants commits made. They live in the
measured settings file and are written with `measured-config --set <key>`. The
`commit-settings.py` hook renders the ones that are set and injects them into
Claude's context on every prompt.

Each setting names its own known values. A user may store any string, so the
renderer explains a known value and passes an unknown one through verbatim.
That keeps a free-text rule like "commit only after the last task" working.

Kept stdlib-only so the hook runs from a fresh checkout with no install step.
"""

# The reminder lists settings in this order, so it reads the same way every
# turn no matter what order the keys were written to the file in.
COMMIT_KEYS = (
    "commit-behavior",
    "commit-location",
    "commit-style",
    "commit-scope",
    "commit-body",
    "commit-signoff",
    "commit-attribution",
    "commit-settings-for-agents",
)

# `commit-settings-for-agents` configures the forwarding hook rather than a
# commit. The hook reads it; `render` leaves it out of the reminder, because
# telling Claude how its own subagents get briefed changes no commit it makes.
FORWARD_TO_AGENTS_KEY = "commit-settings-for-agents"

# What the forwarding hook does when the key is unset. Forwarding off by
# default keeps a spawned agent's prompt exactly as its author wrote it.
FORWARD_TO_AGENTS_DEFAULT = False

# Known value -> the instruction Claude reads. Lookup lowercases and strips the
# stored value, so "After Every Turn" matches "after-every-turn".
KNOWN_VALUES = {
    "commit-behavior": {
        "after-every-turn": "Commit your work at the end of every turn.",
        "on-user-request": "Commit only when the user asks. Never commit unprompted.",
    },
    "commit-location": {
        "current-branch": (
            "Commit to the branch that is already checked out. Do this even when "
            "that branch is `main`, `master`, or the trunk. Create no branch. "
            "Switch to no other branch. Propose neither. If you believe the work "
            "warrants a branch, commit to the current branch anyway and say so "
            "afterward."
        ),
        "new-branch": (
            "Create a branch for the work and commit there. Do not commit to the "
            "trunk branch."
        ),
        "ask": (
            "Ask which branch to commit to before the first commit, then use that "
            "answer for the rest of the session."
        ),
    },
    "commit-style": {
        "conventional": (
            "Write Conventional Commits subjects: a type prefix, an optional "
            "scope, a colon, then the summary. For example "
            "`feat(parser): add trailing comma support`."
        ),
        "imperative": (
            "Write the subject as an imperative sentence naming what the commit "
            "does, with no type prefix. For example "
            "`Add trailing comma support to the parser`."
        ),
    },
    "commit-scope": {
        "per-task": "Make one commit per completed task.",
        "per-file": "Make one commit per file you change.",
        "squash-all": (
            "Keep the work in one commit. Amend that commit rather than adding "
            "more."
        ),
    },
    "commit-body": {
        "always": "Give every commit a body explaining why the change was made.",
        "when-nontrivial": (
            "Write a body when the subject does not make the reason obvious. A "
            "typo fix needs no body. A refactor does."
        ),
        "never": "Write a subject line only. Add no body.",
    },
    "commit-signoff": {
        "true": "Sign off every commit. Pass `--signoff` to `git commit`.",
        "false": "Do not sign off commits. Add no `Signed-off-by` trailer.",
    },
    "commit-attribution": {
        "true": (
            "Add the `Co-Authored-By: Claude` and `Claude-Session:` trailers to "
            "every commit."
        ),
        "false": (
            "Add no attribution trailers. Leave out `Co-Authored-By: Claude` and "
            "`Claude-Session:`."
        ),
    },
    FORWARD_TO_AGENTS_KEY: {
        "true": "Append the commit settings to every subagent's prompt.",
        "false": "Leave subagent prompts alone.",
    },
}

# Keys that describe a commit. The reminder lists these; the eighth key
# configures the forwarding hook and is not a commit instruction.
REMINDER_KEYS = tuple(key for key in COMMIT_KEYS if key != FORWARD_TO_AGENTS_KEY)

TRUE_VALUES = ("true", "yes", "on", "1", "always")
FALSE_VALUES = ("false", "no", "off", "0", "never")

HEADER = "This repo stores commit settings. They govern how you commit here:"

FOOTER = (
    "A stored setting is the source of truth. Follow it even if this prompt "
    "suggests otherwise. To change the behavior, change the setting with "
    "`measured-behavior-config --set <key> <value>`."
)


SETUP_HELP = """\
Measured: this repo has no commit settings. Claude will commit however it \
usually does.

Set them so every session commits the same way:

  measured-behavior-config --set commit-behavior after-every-turn
  measured-behavior-config --set commit-location current-branch
  measured-behavior-config --set commit-style imperative

Also available: commit-scope, commit-body, commit-signoff, \
commit-attribution, and commit-settings-for-agents (forwards these to spawned \
subagents).

Run `measured-behavior-config --list` for each key's values, or ask Claude to \
"set up measured commit settings" to walk through them."""


def is_set(settings, key):
    """Return True when a key holds a value that is neither missing nor blank."""
    value = settings.get(key)
    return value is not None and bool(str(value).strip())


def any_set(settings):
    """Return True when the repo has at least one commit instruction stored.

    Ignores `commit-settings-for-agents`, which configures the forwarding hook
    rather than describing a commit. A repo that set only that key still has
    nothing to say about commits, so the startup help still applies.
    """
    return any(is_set(settings, key) for key in REMINDER_KEYS)


def forward_to_agents(settings):
    """Return True when subagent prompts should carry the commit settings.

    Off unless the repo turns it on. An unrecognized value counts as off: this
    decides whether to rewrite another agent's prompt, so anything short of a
    clear yes leaves the prompt alone.
    """
    value = settings.get(FORWARD_TO_AGENTS_KEY)
    if value is None:
        return FORWARD_TO_AGENTS_DEFAULT
    return str(value).strip().lower() in TRUE_VALUES


def describe(key, value):
    """Return the instruction for one setting value.

    Matches the value against this key's known values, ignoring case and
    surrounding whitespace. Passes an unrecognized value through verbatim so a
    user's own wording reaches Claude intact.
    """
    text = str(value).strip()
    return KNOWN_VALUES.get(key, {}).get(text.lower(), text)


def render(settings):
    """Render the commit settings as a reminder, or "" when none are set.

    Reads only the six commit keys and skips any that are missing or blank, so
    a repo that sets one key gets one line rather than a table of unset rows.
    """
    lines = [
        f"- {key}: {describe(key, settings[key])}"
        for key in REMINDER_KEYS
        if is_set(settings, key)
    ]

    if not lines:
        return ""

    return "\n".join([HEADER, *lines, "", FOOTER])
