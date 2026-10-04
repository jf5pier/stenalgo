"""Plover steno string -> the Stenalgo key ids of `src.keyboard` (the index into `KEYS`)."""
from __future__ import annotations

from ._generated_keys import IMPLICIT_HYPHEN_KEYS, KEYS

_IMPLICIT = frozenset(IMPLICIT_HYPHEN_KEYS)


def _letter(name: str) -> str:
    return name.strip("-")


def parseStroke(steno: str) -> tuple[int, ...] | None:
    """The sorted key ids of one RTFCRE stroke, None when it is not a stroke of this system (the empty
    prefix stroke included). Same reading as Plover: letters in `KEYS` order, left-bank keys before the first
    implicit-hyphen key or `-`, right-bank keys after."""
    if not steno:
        return None
    out: list[int] = []
    start = 0
    right = False
    for ch in steno:
        if ch == "-":
            if right:
                return None
            right = True
            continue
        for j in range(start, len(KEYS)):
            name = KEYS[j]
            if _letter(name) != ch:
                continue
            if name in _IMPLICIT or ("-" not in name) \
                    or (name.endswith("-") and not right) or (name.startswith("-") and right):
                break
        else:
            return None
        out.append(j)
        start = j + 1
        if name in _IMPLICIT:
            right = True
    return tuple(out)


def parseOutline(key: tuple[str, ...]) -> tuple[tuple[int, ...], ...] | None:
    strokes = tuple(parseStroke(s) for s in key)
    if any(s is None for s in strokes):
        return None
    return strokes  # type: ignore[return-value]
