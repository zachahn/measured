"""Shared logic for the measured-note CLI.

Walks up the ancestor process chain to find the nearest `claude` process and
derives a per-session state directory from that PID and its start time. Also
exposes the note read/edit/append primitives used by the CLI.

Kept stdlib-only so the script can be invoked from a fresh checkout without
any install step.
"""

import ctypes
import os
import pathlib
import subprocess
import sys
from datetime import datetime

CLAUDE_PROCESS_NAME = "claude"
MAX_ANCESTOR_DEPTH = 64

NOTE_DRAFT = "ticket-draft"
NOTE_TICKET = "ticket"
NOTE_FILENAMES = {
    NOTE_DRAFT: "TICKET-DRAFT.md",
    NOTE_TICKET: "TICKET.md",
}


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
    path = state_root() / f"{start_time}-{claude_pid}-note"
    path.mkdir(parents=True, exist_ok=True)
    return path


def note_path(directory: pathlib.Path, note_type: str) -> pathlib.Path:
    return directory / NOTE_FILENAMES[note_type]


def read_note(directory: pathlib.Path, note_type: str) -> str:
    target = note_path(directory, note_type)
    if not target.is_file():
        raise FileNotFoundError(f"{target.name} not set")
    return target.read_text()


def append_note(directory: pathlib.Path, note_type: str, text: str) -> pathlib.Path:
    target = note_path(directory, note_type)
    with open(target, "a") as f:
        f.write(text)
    return target


def edit_note(
    directory: pathlib.Path, note_type: str, old: str, new: str, replace_all: bool
) -> tuple[pathlib.Path, int]:
    if old == new:
        raise ValueError("old and new must differ")
    target = note_path(directory, note_type)
    if not target.is_file():
        raise FileNotFoundError(f"{target.name} not set")
    text = target.read_text()
    count = text.count(old)
    if count == 0:
        raise ValueError("old string not found")
    if not replace_all and count > 1:
        raise ValueError(
            f"old string appears {count} times; pass --replace-all or add more context"
        )
    updated = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    target.write_text(updated)
    return target, (count if replace_all else 1)
