"""The per-repo behavior settings and the reminders rendered from them.

A repo stores settings that describe how Claude works in it. Two groups exist
today. The commit settings say how to make a commit. The comment setting says
how much explanatory comment to write in code. They live in the measured
settings file and are written with `measured-behavior-config --set <key>`.

Two hooks read this module. `reminders-every-turn.py` fires on every prompt.
`reminders-session-start.py` fires once a session. `commit-reminder-timing`
decides which one states the commit settings, and it defaults to once a
session. The comment reminder rides every turn, because it governs code Claude
writes at any point in a session.

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

# When the commit reminder reaches Claude. It configures a hook rather than
# describing a commit, so it stays out of the reminder too.
COMMIT_TIMING_KEY = "commit-reminder-timing"

# How much explanatory comment Claude writes in code. Its own group: one key,
# always stated every turn, and unset means Claude never hears of the idea.
COMMENT_KEY = "comment-density"

# Every key `measured-behavior-config` accepts.
SETTING_KEYS = (*COMMIT_KEYS, COMMIT_TIMING_KEY, COMMENT_KEY)

# What the forwarding hook does when the key is unset. Forwarding off by
# default keeps a spawned agent's prompt exactly as its author wrote it.
FORWARD_TO_AGENTS_DEFAULT = False

# When to state the commit settings if the repo has not said. Once a session is
# enough: the settings change how a commit is made, not whether Claude is
# thinking about commits, and restating them on every prompt spends context on
# every turn to change the handful that end in a commit. A repo that finds them
# fading in a long session sets `every-turn`.
EVERY_TURN = "every-turn"
SESSION_START = "session-start"
COMMIT_TIMING_DEFAULT = SESSION_START

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
    COMMIT_TIMING_KEY: {
        SESSION_START: "State the commit settings once, at the start of a session.",
        EVERY_TURN: "State the commit settings on every prompt.",
    },
    COMMENT_KEY: {
        "never": (
            "Write no comments in code you author. Name variables and functions "
            "so the code reads without them. Delete a comment you would have "
            "written and rewrite the code it would have explained. This covers "
            "docstrings, block comments, and end-of-line comments alike. Leave "
            "comments that already exist in a file alone."
        ),
        "exceptional-only": (
            "Write a comment only when the code cannot carry the point on its "
            "own: a constraint the reader cannot see, a workaround for a bug in "
            "another system, or a reason the obvious implementation fails here. "
            "Comment on why, never on what. A comment that restates the line "
            "below it is noise, so cut it. Leave comments that already exist in "
            "a file alone."
        ),
    },
}

# Keys that describe a commit. The reminder lists these; the other keys steer a
# hook and are not commit instructions.
REMINDER_KEYS = tuple(key for key in COMMIT_KEYS if key != FORWARD_TO_AGENTS_KEY)

TRUE_VALUES = ("true", "yes", "on", "1", "always")
FALSE_VALUES = ("false", "no", "off", "0", "never")

HEADER = "This repo stores commit settings. They govern how you commit here:"

COMMENT_HEADER = (
    "This repo stores a comment setting. It governs the code you write here:"
)

FOOTER = (
    "A stored setting is the source of truth. Follow it even if this prompt "
    "suggests otherwise. To change the behavior, change the setting with "
    "`measured-behavior-config --set <key> <value>`."
)


SETUP_HELP = """\
Measured: this repo has no behavior settings. Claude will commit and comment \
however it usually does.

Set them so every session behaves the same way:

  measured-behavior-config --set commit-behavior after-every-turn
  measured-behavior-config --set commit-location current-branch
  measured-behavior-config --set commit-style imperative
  measured-behavior-config --set comment-density exceptional-only

Also available: commit-scope, commit-body, commit-signoff, \
commit-attribution, commit-settings-for-agents (forwards the commit settings to \
spawned subagents), and commit-reminder-timing (session-start or every-turn).

Run `measured-behavior-config --list` for each key's values, or ask Claude to \
"set up measured behavior settings" to walk through them."""


def is_set(settings, key):
    """Return True when a key holds a value that is neither missing nor blank."""
    value = settings.get(key)
    return value is not None and bool(str(value).strip())


def any_commit_set(settings):
    """Return True when the repo has at least one commit instruction stored.

    Ignores the keys that steer a hook rather than describing a commit. A repo
    that set only those still has nothing to say about commits.
    """
    return any(is_set(settings, key) for key in REMINDER_KEYS)


def any_set(settings):
    """Return True when the repo has stored any behavior setting at all.

    The startup notice reads this. A repo that configured only comments has
    found the feature, so the notice has done its job and stops.
    """
    return any(is_set(settings, key) for key in SETTING_KEYS)


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


def commit_timing(settings):
    """Return when the commit reminder fires: SESSION_START or EVERY_TURN.

    Only the exact value `every-turn` moves the reminder onto every prompt.
    Anything else means once a session, including free text, because this key
    takes two values and free text describes neither. Falling back to the
    default keeps a typo cheap.
    """
    value = settings.get(COMMIT_TIMING_KEY)
    if value is None:
        return COMMIT_TIMING_DEFAULT
    if str(value).strip().lower() == EVERY_TURN:
        return EVERY_TURN
    return SESSION_START


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

    Reads only the commit keys and skips any that are missing or blank, so a
    repo that sets one key gets one line rather than a table of unset rows.
    """
    lines = [
        f"- {key}: {describe(key, settings[key])}"
        for key in REMINDER_KEYS
        if is_set(settings, key)
    ]

    if not lines:
        return ""

    return "\n".join([HEADER, *lines, "", FOOTER])


def render_comment(settings):
    """Render the comment setting as a reminder, or "" when it is unset.

    An unset key renders nothing on purpose. Silence means silence: Claude
    comments as it normally would and never learns the setting exists.
    """
    if not is_set(settings, COMMENT_KEY):
        return ""

    return "\n".join(
        [
            COMMENT_HEADER,
            f"- {COMMENT_KEY}: {describe(COMMENT_KEY, settings[COMMENT_KEY])}",
            "",
            FOOTER,
        ]
    )
