"""Read and write the measured settings files.

Settings live in two scopes. The repo scope holds one file per project
directory. The global scope holds one file for every project. A hook reads the
merge of the two: the global file provides defaults, and a repo overrides the
keys it sets.

Both plugins share the repo file. `measured` writes its own keys through
`measured-config`, and `measured-behavior` writes the commit keys through
`measured-behavior-config`. Neither imports the other, so either installs and
runs without the other present. The global file belongs to `measured-behavior`
alone; `measured` has no global scope.

Both plugins derive the same repo path from the same rule: encode the project's
absolute path the way Claude Code names its `projects/<encoded-cwd>/` dirs,
then look under the measured state root. `measured/lib/session_lib.py` holds
the writing side of that rule. The two derivations are duplicated on purpose,
because neither plugin may import the other, and
`measured-behavior/test/test_behavior_settings.py` asserts they agree.

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


def global_settings_path() -> pathlib.Path:
    """The settings file that applies to every project (does not create it).

    Sits beside `projects/` under the state root, so the global file and the
    per-repo files move together when XDG_STATE_HOME changes.
    """
    return state_root() / SETTINGS_FILENAME


def _load(path: pathlib.Path) -> dict:
    """Return the JSON object stored at a path, or {} for anything else.

    Returns {} rather than raising when the file is missing, unreadable, or
    holds anything but a JSON object, so a hook never fails on a malformed
    settings file.
    """
    try:
        raw = path.read_text()
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_settings(cwd) -> dict:
    """Return the settings stored for a working directory, or {} if none."""
    return _load(repo_dir_for_project(cwd) / SETTINGS_FILENAME)


def load_global_settings() -> dict:
    """Return the settings stored for every project, or {} if none."""
    return _load(global_settings_path())


def load_effective_settings(cwd) -> dict:
    """Return the settings in force for a working directory.

    The global file supplies defaults and the repo file overrides them, key by
    key. A repo key holding None or a blank string overrides nothing, matching
    `behavior_settings.is_set`, which already treats a blank value as unset.
    Without that rule a blank repo value would mask a global one, and no
    command writes a blank on purpose.
    """
    settings = load_global_settings()
    for key, value in load_settings(cwd).items():
        if value is not None and str(value).strip():
            settings[key] = value
    return settings


def _write(path: pathlib.Path, settings: dict) -> None:
    """Write a settings object, creating the directory that holds it.

    Matches `session_lib.set_setting`'s on-disk format: pretty-printed JSON
    with a trailing newline.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")


def set_setting(cwd, key, value) -> dict:
    """Set one repo setting, write the file, and return the full settings dict.

    Passing value=None deletes the key. Reads the file first and writes the
    whole object back, so keys the `measured` plugin owns survive a write from
    here.
    """
    settings = load_settings(cwd)
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value

    _write(repo_dir_for_project(cwd) / SETTINGS_FILENAME, settings)
    return settings


def set_global_setting(key, value) -> dict:
    """Set one global setting, write the file, and return the settings dict.

    Passing value=None deletes the key. Deleting a global key returns every
    repo that was inheriting it to whatever it does with the key unset.
    """
    settings = load_global_settings()
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value

    _write(global_settings_path(), settings)
    return settings
