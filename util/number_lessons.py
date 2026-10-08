"""
Number lessons (S10d, the `chiffres` track of `util/export_punctuation_lessons.py`): the digit chords of the two number dictionaries
(`util/export_plover_numbers.py`) as drill items, one lesson set per chord style. Both chord styles teach the number bar
(`plover_stenalgo_pluvier_numbers.json`): Plover English's bar and Pluvier's are the same, and the trainer has no third switch for Lapwing's
numpad (`plover_stenalgo_lapwing_numbers.json`). The scheme of a style is `export_punctuation_lessons.NUMBER_SCHEMES`: "bar" or "lapwing".

A number token of an example (`#2025`) is split into the strokes its style types it with:
* Pluvier: runs of digits that go up in the keyboard order 1 2 3 4 5 0 6 7 8 9 are one stroke each (`#STPH` = 1234);
* Lapwing: a digit followed by up to three zeros is one stroke (`#ER` = 10, `#UR` = 100, `#EUR` = 1000), a lone run of zeros too.
Each stroke is a pseudo mark `n_<digits>` (translation `{&<digits>}`, a glue), so `export_punctuation_lessons.phraseItem` builds the
drill item like any phrase.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

PLUVIER_ORDER = "1234506789"
GLUE = re.compile(r"^\{&(\d+)\}$")


def pluvierSplit(digits: str) -> list[str]:
    """Runs of digits that strictly go up in the keyboard order: one stroke each."""
    runs: list[str] = []
    for digit in digits:
        if runs and PLUVIER_ORDER.index(digit) > PLUVIER_ORDER.index(runs[-1][-1]):
            runs[-1] += digit
        else:
            runs.append(digit)
    return runs


def lapwingSplit(digits: str) -> list[str]:
    """A digit with the (up to three) zeros that follow it, one stroke; zeros with no digit before them, up to three per stroke."""
    pieces: list[str] = []
    i = 0
    while i < len(digits):
        j = i + 1
        while j < len(digits) and digits[j] == "0" and j - i <= 3 and (digits[i] != "0" or j - i < 3):
            j += 1
        pieces.append(digits[i:j])
        i = j
    return pieces


def splitNumber(scheme: str, digits: str) -> list[str]:
    return lapwingSplit(digits) if scheme == "lapwing" else pluvierSplit(digits)


def glueChords(translationChords: dict[str, str]) -> dict[str, list[str]]:
    """{digits: [chords]} of a number dictionary's `{&digits}` entries (the plain glues; the `{^ ^}` spaced ones are not)."""
    chords: dict[str, list[str]] = defaultdict(list)
    for chord, translation in translationChords.items():
        match = GLUE.match(translation)
        if match:
            chords[match.group(1)].append(chord)
    return {digits: sorted(group, key=lambda c: (len(c), c)) for digits, group in chords.items()}


def numberEntries(chords: dict[str, list[str]]) -> dict[str, dict[str, Any]]:
    """The pseudo marks of a number dictionary, keyed by slug `n_<digits>`: translation, name, glyph, primary chord, all chords."""
    entries: dict[str, dict[str, Any]] = {}
    for digits, group in chords.items():
        entries[f"n_{digits}"] = {
            "slug": f"n_{digits}", "translation": "{&" + digits + "}",
            "name": ("le chiffre " if len(digits) == 1 else "le nombre ") + digits,
            "family": "chiffres", "glyph": digits, "keywords": ["chiffre", "nombre"],
            "primary": group[0], "chords": group, "own": group,
            "output": digits}
    return entries


def expandTokens(scheme: str, tokens: list[str], entries: dict[str, dict[str, Any]]) -> list[str]:
    """The example's tokens with every number `#<digits>` replaced by the `@n_<digits>` marks of its strokes."""
    out: list[str] = []
    for token in tokens:
        if token.startswith("#"):
            for piece in splitNumber(scheme, token[1:]):
                if f"n_{piece}" not in entries:
                    raise ValueError(f"no chord for the stroke {piece!r} of the number {token!r} in the {scheme} scheme")
                out.append(f"@n_{piece}")
        else:
            out.append(token)
    return out
