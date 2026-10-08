"""
Number dictionaries for the Stenalgo French system, in two files (docs/PLOVER_COMPLEMENTS.md), converted KEY TO KEY like the
punctuation (`util/export_plover_complements.py`: each Ireland key becomes the Stenalgo key on the same Gemini PR button, the
number bar becomes the Stenalgo `#` key):

* `plover_stenalgo_lapwing_numbers.json`: `resources/reference/lapwing-numbers.json` (Lapwing's right-hand numpad `#-R` 1 ... `#-L` 9,
  `E` tens, `U` hundreds, `EU` thousands, the hours). The English "o'clock" and the `:00` of the hours become the French "h".
* `plover_stenalgo_pluvier_numbers.json`: Pluvier's number bar, which "works exactly like common Plover theory" (Tao.md, Lesson 9):
  `S T P H A O -F -P -L -T` + bar = 1 2 3 4 5 0 6 7 8 9, several digits in one stroke when they follow the keyboard order
  (`#STPH` = 1234; the top `S` is the Stenalgo `k-`: `k-#` is 1). Pluvier's glued comma and period (`-FRBGS` / `-RPBGS`) are in the Pluvier punctuation set. Its phonetic number words (`SUN`,
  `PHRIL`, the Tao.md table) are not repeated: the theory spells the number words itself (`cent`, `mille`, ...).

The number chords are reserved in the star/hash mark assignment (`reservedNumberStrokes`), so no theory word takes one; the filter below
(not pressable, equals a theory outline or the first stroke of one, already in the punctuation or command files: dropped and
reported) is the safety net and reports nothing on a consistent build. Either file works alone; the plugin lists the Pluvier one above the Lapwing one, so a chord both
define means the Pluvier digits.

Run: python -m util.export_plover_numbers
Requires starboard3h.json, plover_stenalgo_dictionary.json and the punctuation / commands files (util.export_plover_complements).
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_plover_complements import GEMINI, KEYBOARD_JSON, STAR_BUTTONS, THEORY, COMMANDS_OUT, PUNCTUATION_OUT, convertOutline, pressable, \
    starboardKeys

LAPWING_SOURCE = "resources/reference/lapwing-numbers.json"
LAPWING_OUT = "plover_stenalgo_lapwing_numbers.json"
PLUVIER_OUT = "plover_stenalgo_pluvier_numbers.json"

# The number-bar keys in keyboard order, each with its digit: S T P H A | O | -F -P -L -T = 1 2 3 4 5 | 0 | 6 7 8 9
BAR_KEYS: tuple[tuple[str, str], ...] = (("S", "1"), ("T", "2"), ("P", "3"), ("H", "4"), ("A", "5"), ("O", "0"),
                                         ("-F", "6"), ("-P", "7"), ("-L", "8"), ("-T", "9"))
# Pluvier's top-row `S` is the Stenalgo `k-` (the Gemini #C button), not `s-` (S2-): `k-#` for 1 (2026-10-07). Lapwing's chords keep GEMINI.
PLUVIER_GEMINI = {**GEMINI, "S": "#C"}


def frenchHours(translation: str) -> str:
    """Lapwing's English hours in French: `10 o'clock` -> `10 h`, `10:00` -> `10 h`."""
    return translation.replace(" o'clock", " h").replace(":00", " h")


def barStroke(keys: tuple[tuple[str, str], ...]) -> str:
    """The Ireland stroke of a number bar pressed with these keys (`#STPH`, `#S-F`, `#AO`)."""
    left = "".join(k for k, _ in keys if not k.startswith("-") and k not in "AO")
    vowels = "".join(k for k, _ in keys if k in ("A", "O"))
    right = "".join(k[1:] for k, _ in keys if k.startswith("-"))
    return "#" + left + vowels + ("-" if right and not vowels else "") + right


def pluvierEntries() -> dict[str, str]:
    """{Ireland outline: translation}: every subset of the ten bar keys (digits in keyboard order) and the glue chords."""
    entries = {barStroke(subset): "{&" + "".join(d for _, d in subset) + "}"
               for size in range(1, len(BAR_KEYS) + 1) for subset in combinations(BAR_KEYS, size)}
    return entries


def convertEntries(entries: dict[str, str], starboard: Starboard, buttonKey: dict[str, int], theoryOutlines: set[str],
                   theoryFirstStrokes: set[str], taken: set[str], gemini: dict[str, str] = GEMINI) -> dict[str, Any]:
    """{"entries": {chord: translation}, "dropped": [(Ireland outline, reason)]} for the Ireland entries."""
    result: dict[str, Any] = {"entries": {}, "dropped": []}
    for outline, translation in entries.items():
        converted = convertOutline(outline, buttonKey, gemini)
        if converted is None:
            result["dropped"].append((outline, "a key with no Stenalgo counterpart"))
            continue
        for strokes in converted:
            text = renderFinalStrokesToRTFCRE(starboard, strokes)
            reason = ("not pressable" if not all(pressable(starboard, s) for s in strokes) else
                      "equals a theory outline" if text in theoryOutlines else
                      "first stroke of a theory outline" if text.split("/")[0] in theoryFirstStrokes else
                      "already in the punctuation or command files" if text in taken else
                      "already taken by another entry" if text in result["entries"] else "")
            if reason:
                result["dropped"].append((outline, f"{text}: {reason}"))
            else:
                result["entries"][text] = translation
    return result


def reservedNumberStrokes() -> frozenset[frozenset[int]]:
    """The chords no word may type: every stroke, as a set of Stenalgo key indices, of every Pluvier number-bar chord and of every outline of
    the Lapwing file (hours included), converted key to key and unfiltered, that holds the `#` key. The star/hash mark assignment
    (`src.ambiguitychecker.composeReservedKeyStrokesForEntries`) never gives a word a mark that makes its last stroke one of them. The
    Gemini PR buttons are positional (key index -> label), so no generated key file is needed."""
    from util.export_plover_system import GEMINI_PR_LABELS
    buttonKey = {label: index for index, label in enumerate(GEMINI_PR_LABELS)}
    hashKey = buttonKey[STAR_BUTTONS[1]]
    with open(LAPWING_SOURCE, encoding="utf-8") as f:
        sources = ((list(json.load(f)), GEMINI), (list(pluvierEntries()), PLUVIER_GEMINI))
    reserved: set[frozenset[int]] = set()
    for outlines, gemini in sources:
        for outline in outlines:
            for strokes in convertOutline(outline, buttonKey, gemini) or []:
                reserved.update(frozenset(stroke) for stroke in strokes if hashKey in stroke)
    return frozenset(reserved)


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    with open(THEORY, encoding="utf-8") as f:
        theory = json.load(f)
    taken: set[str] = set()
    for path in (PUNCTUATION_OUT, COMMANDS_OUT):
        with open(path, encoding="utf-8") as f:
            taken |= set(json.load(f))
    firstStrokes = {outline.split("/")[0] for outline in theory if "/" in outline}
    buttonKey = starboardKeys(KEYS, GEMINI_PR_KEYMAP)
    with open(LAPWING_SOURCE, encoding="utf-8") as f:
        lapwing = {outline: frenchHours(translation) for outline, translation in json.load(f).items()}
    for name, source, path, gemini in (("Pluvier", pluvierEntries(), PLUVIER_OUT, PLUVIER_GEMINI),
                                       ("Lapwing", lapwing, LAPWING_OUT, GEMINI)):
        built = convertEntries(source, starboard, buttonKey, set(theory), firstStrokes, taken, gemini)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(built["entries"], f, ensure_ascii=False, indent=0, sort_keys=True)
            f.write("\n")
        print(f"Wrote {path} ({len(built['entries'])} of {len(source)} {name} outlines), dropped {len(built['dropped'])}:")
        for outline, reason in built["dropped"]:
            print(f"  {outline}: {reason}")


if __name__ == "__main__":
    main()
