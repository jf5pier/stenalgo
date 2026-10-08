"""
The Stenalgo spelling theory: single-letter typing for French (docs/PLOVER_COMPLEMENTS.md, "Spelling").

A letter stroke is a LEFT-HAND chord (the letter, plus an accent key) + the thumbs (vowels) + one of FOUR right-hand endings:

* the letter is the key of its sound in the layout: b d f g k l m n p s t v w z are their onset chords, `j` is the phoneme /Z/ (`v` + `t`),
  `y` is the glide /j/, `r` the /R/ key; the vowels are their thumb chords (`a` `e` `i` `o`, `u` is the phoneme /y/). `h` `q` `c` `x` have no
  sound of their own: `h` is the `*` key alone, `q` = `k*`, `c` = `s*`, `x` = `ks*` (g + `*`);
* an accent is ONE left-hand key shared by every letter that takes it: acute `w` (é), grave `R` (à è ù), circumflex `*` (â ê î ô û),
  diaeresis `t` (ë ï ü), cedilla `m` (c + cedilla = ç). Those keys are free whenever a thumb is pressed (no consonant letter has one), and
  `&` `%` stay reserved;
* the right hand has two orthogonal gestures: the ROW is the case (top row `-ktnZ` lower case, bottom row `-dRlm` UPPER case) and adding the index
  key (`-j` / `-s`) makes the letter followed by a space.

All 156 strokes (39 letters x 4) are pressable and collide with nothing: not a theory word, not the first stroke of an outline, not punctuation,
command, number or affix abbreviation, not an expression attach key (the check below raises otherwise). `reservedSpellingStrokes` keeps the star/hash
mark assignment from ever turning a word into one (same mechanism as the numbers).

Run: python -m util.export_plover_spelling
Requires starboard3h.json, plover_stenalgo_dictionary.json, the punctuation / commands / number files and the affix dictionary.
Outputs: plover_stenalgo_spelling.json.
"""
from __future__ import annotations

import json
from typing import Any

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_plover_complements import COMMANDS_OUT, KEYBOARD_JSON, PLUVIER_OUT, PUNCTUATION_OUT, THEORY, pressable

SPELLING_OUT = "plover_stenalgo_spelling.json"
AFFIX_DICTIONARY = "plover_stenalgo_affix_dictionary.json"
EXPRESSIONS = "plover_stenalgo_expressions.stenalgo"
OTHER_FILES = (PUNCTUATION_OUT, PLUVIER_OUT, COMMANDS_OUT, "plover_stenalgo_pluvier_numbers.json", "plover_stenalgo_lapwing_numbers.json")
MARK_KEYS = (10, 15)                          # `*` and `#`, the S7 homophone marks

# Letter chords: key indices of the onset bank (2-9), the `*` key (10) and the thumbs (11-14).
LETTERS: dict[str, tuple[int, ...]] = {
    "a": (12,), "e": (14,), "i": (13,), "o": (12, 14), "u": (11, 13), "y": (8, 9),
    "b": (3, 5), "d": (4, 5), "f": (2, 4), "g": (2, 3), "j": (5, 7), "k": (2,), "l": (6, 7), "m": (6,),
    "n": (6, 8), "p": (4,), "r": (8,), "s": (3,), "t": (7,), "v": (5,), "w": (9,), "z": (7, 9),
    "h": (10,), "q": (2, 10), "c": (3, 10), "x": (2, 3, 10),
}
ACCENTS: dict[str, int] = {"acute": 9, "grave": 8, "circumflex": 10, "diaeresis": 7, "cedilla": 6}
ACCENTED: dict[str, tuple[str, str]] = {          # character -> (base letter, accent)
    "é": ("e", "acute"), "à": ("a", "grave"), "è": ("e", "grave"), "ù": ("u", "grave"),
    "â": ("a", "circumflex"), "ê": ("e", "circumflex"), "î": ("i", "circumflex"), "ô": ("o", "circumflex"), "û": ("u", "circumflex"),
    "ë": ("e", "diaeresis"), "ï": ("i", "diaeresis"), "ü": ("u", "diaeresis"), "ç": ("c", "cedilla"),
}
# The four endings: lower / UPPER x no space / space after.
ENDINGS: dict[str, tuple[int, ...]] = {
    "lower": (18, 20, 22, 24), "upper": (19, 21, 23, 25),
    "lowerSpace": (16, 18, 20, 22, 24), "upperSpace": (17, 19, 21, 23, 25),
}


def letterChords() -> dict[str, tuple[int, ...]]:
    """The left-hand + thumb part of every character."""
    chords = dict(LETTERS)
    for char, (base, accent) in ACCENTED.items():
        chords[char] = tuple(sorted(set(LETTERS[base]) | {ACCENTS[accent]}))
    return chords


def translation(char: str, ending: str) -> str:
    glued = "{&" + (char.upper() if ending.startswith("upper") else char) + "}"
    return glued + "{^ ^}" if ending.endswith("Space") else glued


def strokes() -> dict[tuple[int, ...], str]:
    """Every spelling stroke (sorted key indices) with its translation."""
    return {tuple(sorted(set(keys) | set(ENDINGS[ending]))): translation(char, ending)
            for char, keys in letterChords().items() for ending in ENDINGS}


def reservedSpellingStrokes() -> frozenset[frozenset[int]]:
    """The spelling strokes that hold a mark key (`*` or `#`): no word may take one by its star/hash mark. The others never occur in the
    theory (the check in `build`), a mark-free word stroke is not changed by the mark assignment."""
    return frozenset(frozenset(stroke) for stroke in strokes() if any(key in stroke for key in MARK_KEYS))


def attachKeypresses(path: str = EXPRESSIONS) -> set[frozenset[int]]:
    """Every attach keypress of the expression rules (they may stand alone as a stroke)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    found: set[frozenset[int]] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "keypress" in node:
                found.add(frozenset(node["keypress"]))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(data["rules"])
    return found


def build(starboard: Starboard, taken: set[str], firstStrokes: set[str], attach: set[frozenset[int]],
          numbers: frozenset[str] = frozenset()) -> dict[str, str]:
    """The spelling dictionary; raises on an unpressable stroke, a duplicate or a collision (the design guarantees none)."""
    entries: dict[str, str] = {}
    problems = []
    for stroke, text in strokes().items():
        chord = renderFinalStrokesToRTFCRE(starboard, (stroke,))
        if not pressable(starboard, stroke):
            problems.append(f"{chord} {text}: not pressable")
        elif chord in entries:
            problems.append(f"{chord} {text}: same chord as {entries[chord]}")
        elif chord in taken or chord in firstStrokes or chord in numbers or frozenset(stroke) in attach:
            problems.append(f"{chord} {text}: collides with the theory, a complement, a number or an attach key")
        entries[chord] = text
    if problems:
        raise ValueError("spelling theory conflicts:\n" + "\n".join(problems))
    return entries


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    taken: set[str] = set()
    firstStrokes: set[str] = set()
    for path in (THEORY, AFFIX_DICTIONARY):
        with open(path, encoding="utf-8") as f:
            for outline in json.load(f):
                taken.add(outline)
                firstStrokes.add(outline.split("/")[0])
    for path in OTHER_FILES:
        with open(path, encoding="utf-8") as f:
            taken |= set(json.load(f))
    from util.export_plover_numbers import reservedNumberStrokes
    numbers = frozenset(renderFinalStrokesToRTFCRE(starboard, (tuple(sorted(stroke)),)) for stroke in reservedNumberStrokes())
    built = build(starboard, taken, firstStrokes, attachKeypresses(), numbers)
    with open(SPELLING_OUT, "w", encoding="utf-8") as f:
        json.dump(built, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")
    print(f"Wrote {SPELLING_OUT} ({len(built)} strokes, {len(letterChords())} characters x {len(ENDINGS)} endings).")


if __name__ == "__main__":
    main()
