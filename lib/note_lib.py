"""Note read/edit/append primitives used by the measured-note CLI.

Each note type maps to a single fixed filename inside the per-session
directory provided by session_lib.

Kept stdlib-only so the script can be invoked from a fresh checkout without
any install step.
"""

import pathlib

NOTE_TICKET = "ticket"
NOTE_FILENAMES = {
    NOTE_TICKET: "TICKET.md",
}


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
