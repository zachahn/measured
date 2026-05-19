"""Shared logic for the measured-agenda CLI.

Agenda items live as markdown files in a per-session subdirectory:

    <session>/AGENDA/0010.md
    <session>/AGENDA/0020.md

The numeric filename controls sort order and nothing else — it is not
intended to be human-meaningful. The *title* lives on the file's first line
as a `# Title` markdown header, and that header is the canonical identity.
LLM callers can rename an item by rewriting the first line via --update.

Invariants enforced on every write:
  - The first line is `# <title>` (non-empty after the `# `).
  - Every item's title is unique within the directory.

Kept stdlib-only so the script runs from a fresh checkout.
"""

import pathlib
import re

AGENDA_DIRNAME = "AGENDA"
SORT_STEP = 10
SORT_WIDTH = 4
SORT_MAX = 10**SORT_WIDTH - 1

_FILENAME_RE = re.compile(r"^(\d+)\.md$")
_HEADER_RE = re.compile(r"^#[ \t]+(\S.*?)[ \t]*$")


def agenda_dir(session: pathlib.Path) -> pathlib.Path:
    path = session / AGENDA_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_filename(name: str) -> int | None:
    m = _FILENAME_RE.match(name)
    return int(m.group(1)) if m else None


def _read_title(path: pathlib.Path) -> str:
    with open(path) as f:
        first = f.readline().rstrip("\n")
    m = _HEADER_RE.match(first)
    if not m:
        raise ValueError(f"{path.name} is missing a `# Title` header on line 1")
    return m.group(1)


def list_items(directory: pathlib.Path) -> list[tuple[int, pathlib.Path, str]]:
    """Return (sort, path, title) triples in sort order.

    Files that don't match the NNNN.md naming are skipped. Files that *do*
    match but lack a valid header surface as a ValueError — that's a broken
    item, not a stray file.
    """
    out = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        sort_value = _parse_filename(entry.name)
        if sort_value is None:
            continue
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


def _filename(sort_value: int) -> str:
    return f"{sort_value:0{SORT_WIDTH}d}.md"


def _validate_text(text: str, expect_title: str | None = None) -> str:
    """Confirm `text` starts with a `# Title` line. Return the parsed title.

    If `expect_title` is given, also confirm the parsed title matches it.
    """
    first_line = text.split("\n", 1)[0]
    m = _HEADER_RE.match(first_line)
    if not m:
        raise ValueError("first line must be a `# Title` header")
    title = m.group(1)
    if expect_title is not None and title != expect_title:
        raise ValueError(
            f"first line header {title!r} does not match expected {expect_title!r}"
        )
    return title


def _check_unique(
    items: list[tuple[int, pathlib.Path, str]],
    title: str,
    exclude: pathlib.Path | None = None,
) -> None:
    for _, p, t in items:
        if p == exclude:
            continue
        if t == title:
            raise ValueError(f"agenda item titled {title!r} already exists")


def add_item(directory: pathlib.Path, title: str, body: str) -> pathlib.Path:
    if "\n" in title or "\r" in title:
        raise ValueError("title must not contain newlines")
    if not title.strip():
        raise ValueError("title must not be empty or whitespace")
    items = list_items(directory)
    _check_unique(items, title)
    sort_value = _next_sort(items)
    target = directory / _filename(sort_value)
    if body and not body.endswith("\n"):
        body += "\n"
    target.write_text(f"# {title}\n\n{body}" if body else f"# {title}\n")
    return target


def append_item(directory: pathlib.Path, title: str, text: str) -> pathlib.Path:
    _, path = find_by_title(directory, title)
    with open(path, "a") as f:
        f.write(text)
    # Belt-and-suspenders: the append must not have corrupted the header or
    # duplicated a title. (Appending to EOF can't normally do either, but
    # validate anyway so the invariants are checked at every write site.)
    new_text = path.read_text()
    new_title = _validate_text(new_text, expect_title=title)
    _check_unique(list_items(directory), new_title, exclude=path)
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
    # Validate before committing: the post-edit file must still have a header,
    # and if the title changed it must not collide with another item.
    new_title = _validate_text(updated)
    _check_unique(list_items(directory), new_title, exclude=path)
    path.write_text(updated)
    return path, (count if replace_all else 1)


def remove_item(directory: pathlib.Path, title: str) -> pathlib.Path:
    _, path = find_by_title(directory, title)
    path.unlink()
    return path


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

    path_by_title = {t: p for _, p, t in items}
    targets = [(i + 1) * SORT_STEP for i in range(len(order))]

    # Two-pass rename through temp names so we never collide mid-move.
    staged: list[tuple[pathlib.Path, pathlib.Path]] = []
    for idx, t in enumerate(order):
        current = path_by_title[t]
        final = directory / _filename(targets[idx])
        if current == final:
            continue
        tmp = directory / f".tmp-{idx}-{current.name}"
        current.rename(tmp)
        staged.append((tmp, final))
    for tmp, final in staged:
        tmp.rename(final)

    return directory / _filename(targets[order.index(title)])


def read_item(directory: pathlib.Path, title: str) -> str:
    _, path = find_by_title(directory, title)
    return path.read_text()


def read_all(directory: pathlib.Path) -> str:
    parts = []
    for _, path, _ in list_items(directory):
        parts.append(path.read_text().rstrip("\n"))
    return "\n\n".join(parts) + ("\n" if parts else "")
