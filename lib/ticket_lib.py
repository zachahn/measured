"""Shared logic for the measured-ticket CLI.

Walks up the ancestor process chain to find the nearest `claude` process and
derives a per-session state directory from that PID and its start time. Also
exposes the step/ticket file primitives used by the CLI.

Kept stdlib-only so the script can be invoked from a fresh checkout without
any install step.
"""

import ctypes
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime

CLAUDE_PROCESS_NAME = "claude"
MAX_ANCESTOR_DEPTH = 64
TICKET_FILENAME = "TICKET.md"


def _start_time_linux(pid: int) -> int:
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith("btime "):
                btime = int(line.split()[1])
                break
        else:
            raise RuntimeError("btime not found in /proc/stat")

    with open(f"/proc/{pid}/stat") as f:
        # Field 2 (comm) is wrapped in parens and may itself contain spaces or
        # parens, so split around the LAST ')' rather than splitting on spaces.
        data = f.read()
        rparen = data.rindex(")")
        fields = data[rparen + 2 :].split()
        # Post-comm field index 19 == original stat field 22 (starttime, in ticks).
        starttime_ticks = int(fields[19])

    clk_tck = os.sysconf("SC_CLK_TCK")
    return btime + starttime_ticks // clk_tck


def _start_time_macos(pid: int) -> int:
    # `ps -o lstart=` emits e.g. "Wed May 13 09:37:13 2026" in the local timezone.
    result = subprocess.run(
        ["ps", "-o", "lstart=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError(f"ps returned no start time for pid {pid}")
    dt = datetime.strptime(raw, "%a %b %d %H:%M:%S %Y")
    return int(dt.astimezone().timestamp())


def _start_time_windows(pid: int) -> int:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        creation = ctypes.c_ulonglong()
        exit_t = ctypes.c_ulonglong()
        kernel_t = ctypes.c_ulonglong()
        user_t = ctypes.c_ulonglong()
        ok = kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_t),
            ctypes.byref(kernel_t),
            ctypes.byref(user_t),
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel32.CloseHandle(handle)

    # FILETIME counts 100ns intervals since 1601-01-01 UTC; subtract the offset
    # to the Unix epoch (1970-01-01).
    return creation.value // 10_000_000 - 11_644_473_600


def parent_start_time(pid: int) -> int:
    if sys.platform.startswith("linux"):
        return _start_time_linux(pid)
    if sys.platform == "darwin":
        return _start_time_macos(pid)
    if sys.platform == "win32":
        return _start_time_windows(pid)
    raise RuntimeError(f"unsupported platform: {sys.platform}")


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


def state_root() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("XDG_STATE_HOME") or pathlib.Path.home() / ".local" / "state"
    ) / "measured-claude-plugin"


def session_dir() -> pathlib.Path:
    claude_pid = find_claude_pid(os.getppid())
    start_time = parent_start_time(claude_pid)
    path = state_root() / f"{start_time}-{claude_pid}-ticket"
    path.mkdir(parents=True, exist_ok=True)
    return path


def step_files(directory: pathlib.Path) -> list[pathlib.Path]:
    # Sort by the integer stem so `2.md` doesn't sort after `10.md`. Non-numeric
    # stems sort last, alphabetically, for predictability if anything else lands here.
    def key(p: pathlib.Path) -> tuple[int, int | str]:
        try:
            return (0, int(p.stem))
        except ValueError:
            return (1, p.stem)

    return sorted(directory.glob("*.md"), key=key)


def resolve_step(directory: pathlib.Path, name: str) -> pathlib.Path:
    # Reject anything that isn't a bare filename to avoid path traversal.
    if "/" in name or "\\" in name or name in ("", ".", ".."):
        raise ValueError(f"invalid step name: {name!r}")
    if name == TICKET_FILENAME or name == TICKET_FILENAME.removesuffix(".md"):
        raise ValueError(f"invalid step name: {name!r}")
    if not name.endswith(".md"):
        name = f"{name}.md"
    target = directory / name
    if target.parent != directory or not target.is_file():
        raise FileNotFoundError(f"step not found: {name}")
    return target


def write_step(directory: pathlib.Path, text: str) -> pathlib.Path:
    # Millisecond-precision Unix timestamp; retry on the (rare) collision so
    # two rapid calls don't clobber each other.
    while True:
        ts = time.time_ns() // 1_000_000
        target = directory / f"{ts}.md"
        if target.name == TICKET_FILENAME:
            continue
        try:
            with open(target, "x") as f:
                f.write(text)
            return target
        except FileExistsError:
            time.sleep(0.001)


def ticket_path(directory: pathlib.Path) -> pathlib.Path:
    return directory / TICKET_FILENAME


def write_ticket(directory: pathlib.Path, text: str, force: bool) -> pathlib.Path:
    target = ticket_path(directory)
    mode = "w" if force else "x"
    with open(target, mode) as f:
        f.write(text)
    return target
