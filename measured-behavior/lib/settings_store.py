"""Read and write the per-repo measured settings file.

Both plugins share one settings file per repo. `measured` writes its own keys
through `measured-config`, and `measured-behavior` writes the commit keys
through `measured-behavior-config`. Neither imports the other, so either
installs and runs without the other present.

Both plugins derive the same path from the same rule: encode the project's
absolute path the way Claude Code names its `projects/<encoded-cwd>/` dirs,
then look under the measured state root. `measured/lib/session_lib.py` holds
the writing side of that rule. The two derivations are duplicated on purpose,
because neither plugin may import the other, and
`measured-behavior/test/test_settings_store.py` asserts they agree.

A hook receives the working directory on stdin, so this module takes a cwd
argument and never walks the process tree the way session_lib does.

Kept stdlib-only so it runs from a fresh checkout with no install step.
"""

import json
import os
import pathlib

STATE_DIR_NAME = "measured-claude-plugin"
SETTINGS_FILENAME = "settings.json"


def state_root() -> pathlib.Path:
    """The measured state root, honoring XDG_STATE_HOME.

    Mirrors `session_lib.state_root()`.
    """
    base = os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state"
    return pathlib.Path(base) / STATE_DIR_NAME


def encode_project_path(path: str) -> str:
    """Encode a filesystem path the way Claude Code encodes project dirs.

    `/Users/zach/Projects/measured` -> `-Users-zach-Projects-measured`.
    Mirrors `session_lib.encode_project_path()`.
    """
    return path.replace("/", "-")


def repo_dir_for_project(project_path) -> pathlib.Path:
    """The state dir for a project working directory (does not create it).

    Mirrors `session_lib.repo_dir_for_project()`.
    """
    abspath = os.path.abspath(os.path.expanduser(os.fspath(project_path)))
    return state_root() / "projects" / encode_project_path(abspath)


def load_settings(cwd) -> dict:
    """Return the settings stored for a working directory, or {} if none.

    Returns {} rather than raising when the file is missing, unreadable, or
    holds anything but a JSON object, so a hook never fails on a malformed
    settings file.
    """
    path = repo_dir_for_project(cwd) / SETTINGS_FILENAME
    try:
        raw = path.read_text()
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def set_setting(cwd, key, value) -> dict:
    """Set one setting, write the file, and return the full settings dict.

    Passing value=None deletes the key. Reads the file first and writes the
    whole object back, so keys the `measured` plugin owns survive a write from
    here. Matches `session_lib.set_setting`'s on-disk format: pretty-printed
    JSON with a trailing newline.
    """
    settings = load_settings(cwd)
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value

    repo = repo_dir_for_project(cwd)
    repo.mkdir(parents=True, exist_ok=True)
    (repo / SETTINGS_FILENAME).write_text(json.dumps(settings, indent=2) + "\n")
    return settings
