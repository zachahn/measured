"""Repo-scoped state directory shared by the measured CLIs.

Walks up the ancestor process chain to find the nearest `claude` process and
derives a per-repo state directory from its working directory, the same way
Claude Code names its own `projects/<encoded-cwd>/` dirs. Every Claude session
in a given repo lands in the same place, so the ticketing state persists across
sessions and is shared between them.

That state dir holds one plan directory per planning effort, named
`YYYY-MM-DD-slug`. The caller joins filenames (TICKET.md, ARCHITECTURE.md,
TASK-1.md) to a plan dir itself.

Kept stdlib-only so the scripts can be invoked from a fresh checkout without
any install step.
"""

import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

CLAUDE_PROCESS_NAME = "claude"
MAX_ANCESTOR_DEPTH = 64


def _proc_info_linux(pid: int) -> tuple[int, str]:
    with open(f"/proc/{pid}/stat") as f:
        data = f.read()
    lparen = data.index("(")
    rparen = data.rindex(")")
    comm = data[lparen + 1 : rparen]
    fields = data[rparen + 2 :].split()
    # Post-comm field index 1 == original stat field 4 (ppid).
    ppid = int(fields[1])
    return ppid, comm


def _proc_info_macos(pid: int) -> tuple[int, str]:
    result = subprocess.run(
        ["ps", "-o", "ppid=,comm=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError(f"ps returned no info for pid {pid}")
    ppid_str, _, comm = raw.partition(" ")
    return int(ppid_str), os.path.basename(comm.strip())


def _proc_info_windows(pid: int) -> tuple[int, str]:
    # Shell out to PowerShell rather than wrestle with toolhelp32 via ctypes.
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}') | "
            "ForEach-Object { \"$($_.ParentProcessId) $($_.Name)\" }",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError(f"Win32_Process returned no info for pid {pid}")
    ppid_str, _, comm = raw.partition(" ")
    name = comm.strip()
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return int(ppid_str), name


def proc_info(pid: int) -> tuple[int, str]:
    if sys.platform.startswith("linux"):
        return _proc_info_linux(pid)
    if sys.platform == "darwin":
        return _proc_info_macos(pid)
    if sys.platform == "win32":
        return _proc_info_windows(pid)
    raise RuntimeError(f"unsupported platform: {sys.platform}")


def find_claude_pid(start_pid: int) -> int:
    pid = start_pid
    for _ in range(MAX_ANCESTOR_DEPTH):
        if pid <= 1:
            break
        ppid, comm = proc_info(pid)
        if comm == CLAUDE_PROCESS_NAME:
            return pid
        pid = ppid
    raise RuntimeError(
        f"no '{CLAUDE_PROCESS_NAME}' ancestor found within {MAX_ANCESTOR_DEPTH} hops"
    )


def _pwd_linux(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            data = f.read()
    except OSError:
        return None
    for entry in data.split(b"\0"):
        if entry.startswith(b"PWD="):
            return entry[len(b"PWD=") :].decode("utf-8", errors="replace")
    return None


def _pwd_macos(pid: int) -> str | None:
    # `ps -E` appends the process environment after argv, space-separated —
    # so values with embedded spaces will split. PWD paths with spaces are
    # rare enough to ignore.
    try:
        result = subprocess.run(
            ["ps", "-E", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    for token in result.stdout.split():
        if token.startswith("PWD="):
            return token[len("PWD=") :]
    return None


def claude_pwd(pid: int) -> str:
    """Return the working directory of the Claude process, or fall back to ours.

    Mirrors Claude Code's own `projects/<encoded-cwd>/` convention so that a
    given repo gets a stable on-disk namespace regardless of where Claude
    later cd's. Falls back to `os.getcwd()` on platforms or processes where
    the environment isn't readable (notably Windows).
    """
    if sys.platform.startswith("linux"):
        pwd = _pwd_linux(pid)
    elif sys.platform == "darwin":
        pwd = _pwd_macos(pid)
    else:
        pwd = None
    return pwd or os.getcwd()


def encode_project_path(path: str) -> str:
    """Encode a filesystem path the way Claude Code encodes project dirs.

    `/Users/zach/Code/Spike/measured` -> `-Users-zach-Code-Spike-measured`.
    """
    return path.replace("/", "-")


def state_root() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state"
    ) / "measured-claude-plugin"


def repo_dir_for_project(project_path: str | os.PathLike) -> pathlib.Path:
    """The repo dir for a project working directory (does not create it).

    Encodes the project's *absolute* path the way Claude Code names its own
    `projects/<encoded-cwd>/` dirs, so `repo_dir_for_project(".")` yields the
    current project's root without walking the process tree.
    """
    abspath = os.path.abspath(os.path.expanduser(os.fspath(project_path)))
    return state_root() / "projects" / encode_project_path(abspath)


def _repo_dir_for(claude_pid: int) -> pathlib.Path:
    """The repo dir for an already-resolved Claude pid (does not create it)."""
    return repo_dir_for_project(claude_pwd(claude_pid))


def repo_dir() -> pathlib.Path:
    """Return this repo's state dir — the root of its plan directories.

    Namespaced by Claude's working directory the same way Claude Code names
    its own `projects/<encoded-cwd>/` dirs, so one repo maps to one stable
    location across every session. Holds the `YYYY-MM-DD-slug` plan dirs.
    """
    path = _repo_dir_for(find_claude_pid(os.getppid()))
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_slug(slug: str) -> str:
    """Reduce a free-form slug argument to a kebab-case sanitized slug.

    Lowercases, replaces each run of non-alphanumeric characters with a single
    hyphen, and trims leading and trailing hyphens. Returns "" when nothing
    alphanumeric survives (e.g. "!!!" or "   ").
    """
    return re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")


def new_plan_dir(repo: pathlib.Path, slug: str) -> pathlib.Path:
    """Create and return a `YYYY-MM-DD-slug` plan dir under the state dir.

    Sanitizes the slug, prefixes today's local date, and creates the directory.
    Raises ValueError if the slug sanitizes to empty, and FileExistsError if a
    dir of that exact name already exists (same slug twice in one day).
    """
    sanitized = sanitize_slug(slug)
    if not sanitized:
        raise ValueError(f"slug sanitizes to empty: {slug!r}")
    today = datetime.date.today().isoformat()
    path = repo / f"{today}-{sanitized}"
    path.mkdir(parents=True, exist_ok=False)
    return path


SETTINGS_FILENAME = "settings.json"


def settings_path(repo: pathlib.Path) -> pathlib.Path:
    """The settings file for a repo's state dir (does not create it)."""
    return repo / SETTINGS_FILENAME


def load_settings(repo: pathlib.Path) -> dict:
    """Return the repo's settings as a dict, or {} if none are stored yet.

    Raises ValueError if the file exists but does not hold a JSON object.
    """
    path = settings_path(repo)
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"settings file is not a JSON object: {path}")
    return data


def get_setting(repo: pathlib.Path, key: str):
    """Return one setting's value, or None when it is unset."""
    return load_settings(repo).get(key)


def set_setting(repo: pathlib.Path, key: str, value) -> dict:
    """Set one setting, write the file, and return the full settings dict.

    Passing value=None deletes the key. Writes the whole object back as
    pretty-printed JSON with a trailing newline.
    """
    settings = load_settings(repo)
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value
    settings_path(repo).write_text(json.dumps(settings, indent=2) + "\n")
    return settings
