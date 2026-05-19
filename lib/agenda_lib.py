"""Shared logic for the measured-agenda CLI.

Agenda items live as markdown files in a per-session subdirectory:

    <session>/AGENDA/0010-fix-login.md
    <session>/AGENDA/0020-write-docs.md

The numeric prefix orders the items; the slug after it is derived from the
title. Each file starts with a `# Title` line so the original (un-slugified)
title survives, and the body below is free-form markdown.

Identification is always by *title*, never by filename — callers shouldn't
have to know an item's sort prefix.

Kept stdlib-only, like note_lib, so the script runs from a fresh checkout.
"""

import pathlib
import re

import note_lib

AGENDA_DIRNAME = "AGENDA"
SORT_STEP = 10
SORT_WIDTH = 4
SORT_MAX = 10**SORT_WIDTH - 1

_FILENAME_RE = re.compile(r"^(\d+)-(.*)\.md$")
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


def agenda_dir(session: pathlib.Path) -> pathlib.Path:
    path = session / AGENDA_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(title: str) -> str:
    slug = _SLUG_STRIP_RE.sub("-", title.lower()).strip("-")
    return slug or "item"


def _parse_filename(name: str) -> tuple[int, str] | None:
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    return int(m.group(1)), m.group(2)


def _read_title(path: pathlib.Path) -> str:
    # First line is `# Title`; fall back to the slug if missing.
    with open(path) as f:
        first = f.readline().rstrip("\n")
    if first.startswith("# "):
        return first[2:]
    parsed = _parse_filename(path.name)
    return parsed[1] if parsed else path.stem


def list_items(directory: pathlib.Path) -> list[tuple[int, pathlib.Path, str]]:
    """Return (sort, path, title) triples in sort order."""
    out = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        parsed = _parse_filename(entry.name)
        if parsed is None:
            continue
        sort_value, _ = parsed
        out.append((sort_value, entry, _read_title(entry)))
    out.sort(key=lambda row: row[0])
    return out


def find_by_title(directory: pathlib.Path, title: str) -> tuple[int, pathlib.Path]:
    matches = [(s, p) for s, p, t in list_items(directory) if t == title]
    if not matches:
        raise FileNotFoundError(f"no agenda item titled {title!r}")
    if len(matches) > 1:
        raise ValueError(f"multiple agenda items titled {title!r}")
    return matches[0]


def _next_sort(items: list[tuple[int, pathlib.Path, str]]) -> int:
    if not items:
        return SORT_STEP
    last = items[-1][0]
    candidate = ((last // SORT_STEP) + 1) * SORT_STEP
    if candidate > SORT_MAX:
        raise RuntimeError("agenda is full; renumber required")
    return candidate


def _filename(sort_value: int, title: str) -> str:
    return f"{sort_value:0{SORT_WIDTH}d}-{slugify(title)}.md"


def _write_item(path: pathlib.Path, title: str, body: str) -> None:
    # Body may or may not end in a newline; normalise so the file always does.
    if body and not body.endswith("\n"):
        body += "\n"
    path.write_text(f"# {title}\n\n{body}" if body else f"# {title}\n")


def _item_body(path: pathlib.Path) -> str:
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    if not lines:
        return ""
    # Drop the `# Title` line and a single trailing blank line if present.
    rest = lines[1:]
    if rest and rest[0].strip() == "":
        rest = rest[1:]
    return "".join(rest)


def add_item(directory: pathlib.Path, title: str, body: str) -> pathlib.Path:
    items = list_items(directory)
    if any(t == title for _, _, t in items):
        raise ValueError(f"agenda item titled {title!r} already exists")
    sort_value = _next_sort(items)
    target = directory / _filename(sort_value, title)
    _write_item(target, title, body)
    return target


def append_item(directory: pathlib.Path, title: str, text: str) -> pathlib.Path:
    _, path = find_by_title(directory, title)
    with open(path, "a") as f:
        f.write(text)
    return path


def update_item(
    directory: pathlib.Path, title: str, old: str, new: str, replace_all: bool
) -> tuple[pathlib.Path, int]:
    if old == new:
        raise ValueError("old and new must differ")
    _, path = find_by_title(directory, title)
    text = path.read_text()
    count = text.count(old)
    if count == 0:
        raise ValueError("old string not found")
    if not replace_all and count > 1:
        raise ValueError(
            f"old string appears {count} times; pass --replace-all or add more context"
        )
    updated = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    path.write_text(updated)
    return path, (count if replace_all else 1)


def remove_item(directory: pathlib.Path, title: str) -> pathlib.Path:
    _, path = find_by_title(directory, title)
    path.unlink()
    return path


def _renumber(directory: pathlib.Path) -> list[tuple[int, pathlib.Path, str]]:
    items = list_items(directory)
    # Two-pass rename: first to temporary names, then to final names, so we
    # never collide with an existing file mid-rename.
    temp_paths: list[pathlib.Path] = []
    for idx, (_, path, _) in enumerate(items):
        tmp = path.with_name(f".tmp-{idx}-{path.name}")
        path.rename(tmp)
        temp_paths.append(tmp)
    final: list[tuple[int, pathlib.Path, str]] = []
    for idx, tmp in enumerate(temp_paths):
        title = items[idx][2]
        sort_value = (idx + 1) * SORT_STEP
        new_path = directory / _filename(sort_value, title)
        tmp.rename(new_path)
        final.append((sort_value, new_path, title))
    return final


def move_item(
    directory: pathlib.Path,
    title: str,
    before: str | None,
    after: str | None,
) -> pathlib.Path:
    if (before is None) == (after is None):
        raise ValueError("move requires exactly one of --before or --after")
    items = list_items(directory)
    titles = [t for _, _, t in items]
    if title not in titles:
        raise FileNotFoundError(f"no agenda item titled {title!r}")
    anchor = before if before is not None else after
    if anchor not in titles:
        raise FileNotFoundError(f"no agenda item titled {anchor!r}")
    if anchor == title:
        raise ValueError("cannot move an item relative to itself")

    order = [t for t in titles if t != title]
    anchor_idx = order.index(anchor)
    insert_at = anchor_idx if before is not None else anchor_idx + 1
    order.insert(insert_at, title)

    # Look up each title's current path and compute target sort positions.
    path_by_title = {t: p for _, p, t in items}
    targets = [(i + 1) * SORT_STEP for i in range(len(order))]

    # Stage all renames to temp names, then to final names, to dodge collisions.
    staged: list[tuple[pathlib.Path, pathlib.Path]] = []
    for idx, t in enumerate(order):
        current = path_by_title[t]
        final = directory / _filename(targets[idx], t)
        if current == final:
            continue
        tmp = directory / f".tmp-{idx}-{current.name}"
        current.rename(tmp)
        staged.append((tmp, final))
    for tmp, final in staged:
        tmp.rename(final)

    return directory / _filename(targets[order.index(title)], title)


def read_item(directory: pathlib.Path, title: str) -> str:
    _, path = find_by_title(directory, title)
    return path.read_text()


def read_all(directory: pathlib.Path) -> str:
    parts = []
    for _, path, _ in list_items(directory):
        parts.append(path.read_text().rstrip("\n"))
    return "\n\n".join(parts) + ("\n" if parts else "")


def session_dir() -> pathlib.Path:
    return note_lib.session_dir()
