"""Repo-scoped state directory shared by the measured CLIs.

Walks up the ancestor process chain to find the nearest `claude` process and
derives a per-repo state directory from its working directory, the same way
Claude Code names its own `projects/<encoded-cwd>/` dirs. Every Claude session
in a given repo lands in the same place, so the ticketing state persists across
sessions and is shared between them.

That repo dir holds one `state.sqlite3` (see db.py) plus a PLAN-NNNN
directory per planning effort; completed plans move under ARCHIVE/. Task
content lives in the `.md` files; the database only hands out IDs.

Kept stdlib-only so the scripts can be invoked from a fresh checkout without
any install step.
"""

import os
import pathlib
import re
import subprocess
import sys

import db

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
    """Return this repo's state dir — the root of its ticketing layout.

    Namespaced by Claude's working directory the same way Claude Code names
    its own `projects/<encoded-cwd>/` dirs, so one repo maps to one stable
    location across every session. Holds `state.sqlite3`, the PLAN-NNNN
    directories, and ARCHIVE/.
    """
    path = _repo_dir_for(find_claude_pid(os.getppid()))
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_dir_at(root: str | os.PathLike) -> pathlib.Path:
    """Return a caller-supplied state dir, used verbatim as the repo dir.

    Holds `state.sqlite3`, the PLAN-NNNN directories, and ARCHIVE/ — the
    same layout `repo_dir()` produces, but at an explicit path rather than one
    derived from Claude's working directory. Creates the directory if needed.
    """
    path = pathlib.Path(root).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


ARCHIVE_DIRNAME = "ARCHIVE"
PLAN_DIRNAME = "PLAN-{:04d}"
_PLAN_PATTERN = re.compile(r"\APLAN-(\d+)\Z")
TASK_FILENAME = "TASK-{:04d}.md"
_TASK_PATTERN = re.compile(r"\ATASK-(\d+)\.md\Z")


def parse_ref(ref: str, prefix: str) -> int | None:
    """Parse a plan/task ref to its integer ID, or None if unparseable.

    Accepts the forms a caller naturally has on hand: a bare number ("7"),
    the prefixed stem ("PLAN-7" / "TASK-7"), or a task filename
    ("TASK-7.md"). Case-insensitive on the prefix.
    """
    match = re.fullmatch(
        rf"(?:{prefix}-)?(\d+)(?:\.md)?", ref.strip(), re.IGNORECASE
    )
    return int(match.group(1)) if match else None


def plan_dir(repo: pathlib.Path, plan_id: int) -> pathlib.Path | None:
    """Resolve a plan's directory, active or archived, or None if missing.

    Checks the active location first, then ARCHIVE/ — the folder's location is
    the sole record of whether a plan is archived (the database doesn't
    track it).
    """
    name = PLAN_DIRNAME.format(plan_id)
    active = repo / name
    if active.is_dir():
        return active
    archived = repo / ARCHIVE_DIRNAME / name
    if archived.is_dir():
        return archived
    return None


def new_plan(repo: pathlib.Path, conn) -> pathlib.Path:
    """Allocate the next plan ID and create its (active) directory."""
    plan_id = db.allocate_plan(conn)
    path = repo / PLAN_DIRNAME.format(plan_id)
    path.mkdir(parents=True, exist_ok=False)
    return path


def new_task(directory: pathlib.Path, conn, plan_id: int) -> pathlib.Path:
    """Allocate the next global task ID and create its TASK-NNNN.md file.

    The ID comes from the shared database, so it is unique across every plan
    in the repo. The file is created empty for the caller to Write into.
    """
    task_id = db.allocate_task(conn, plan_id)
    path = directory / TASK_FILENAME.format(task_id)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.close(fd)
    return path


def resolve_task_file(directory: pathlib.Path, ref: str) -> pathlib.Path | None:
    """Resolve a task ref to its full path within a project dir, or None.

    Normalizes the ref to the canonical zero-padded filename so that "7",
    "TASK-7", and "TASK-0007.md" all resolve to the same file.
    """
    task_id = parse_ref(ref, "TASK")
    if task_id is None:
        return None
    path = directory / TASK_FILENAME.format(task_id)
    return path if path.is_file() else None


def archive_plan(repo: pathlib.Path, plan_id: int) -> pathlib.Path:
    """Move a plan's directory under ARCHIVE/. Returns the new path.

    Raises if the plan isn't active (already archived or never existed) or
    an archived copy already sits in the way.
    """
    name = PLAN_DIRNAME.format(plan_id)
    src = repo / name
    if not src.is_dir():
        raise FileNotFoundError(f"no active plan {name}")
    dest_parent = repo / ARCHIVE_DIRNAME
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / name
    if dest.exists():
        raise FileExistsError(f"{name} already exists under {ARCHIVE_DIRNAME}/")
    src.rename(dest)
    return dest


def unarchive_plan(repo: pathlib.Path, plan_id: int) -> pathlib.Path:
    """Move a plan's directory back out of ARCHIVE/. Returns the new path.

    Raises if no archived copy exists or an active one already sits in the way.
    """
    name = PLAN_DIRNAME.format(plan_id)
    src = repo / ARCHIVE_DIRNAME / name
    if not src.is_dir():
        raise FileNotFoundError(f"no archived plan {name}")
    dest = repo / name
    if dest.exists():
        raise FileExistsError(f"active {name} already exists")
    src.rename(dest)
    return dest
