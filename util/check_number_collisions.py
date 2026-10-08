"""
Diagnostic: which words, punctuation marks and commands collide with the number chords.

Every Pluvier number-bar chord (all 1023 subsets of the ten bar keys, `util.export_plover_numbers.pluvierEntries`) and every Lapwing
number entry (`i#`, `e#`, `ie#` and the numpad chords, hours included) is converted
key to key WITHOUT the collision filter -- so `@#` and `a#` count as numbers -- and compared with the stock dictionary, the
punctuation and the commands. A chord can collide three ways: it IS an entry (the number would replace it, or be shadowed),
it is the FIRST STROKE of a multi-stroke theory outline (the number would hide that word's start), or it is not pressable.

Run: python -m util.check_number_collisions            # the summary and every collision
     python -m util.check_number_collisions 12 5 @#    # the chord and the collisions of digit strings / chords
Requires starboard3h.json, plover_stenalgo_dictionary.json and the punctuation / commands files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_plover_complements import (COMMANDS_OUT, KEYBOARD_JSON, PUNCTUATION_OUT, THEORY, convertOutline, pressable,
                                            starboardKeys)
from util.export_plover_numbers import LAPWING_SOURCE, PLUVIER_GEMINI, frenchHours, pluvierEntries
from util.export_plover_complements import GEMINI


def load(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        data: dict[str, str] = json.load(f)
    return data


def collisions(chord: str, theory: dict[str, str], punctuation: dict[str, str], commands: dict[str, str],
               firstStrokes: dict[str, list[str]]) -> list[str]:
    """Human-readable collisions of one chord (empty list: free)."""
    found = []
    if chord in theory:
        found.append(f"word «{theory[chord]}»")
    if chord in punctuation:
        found.append(f"punctuation {punctuation[chord]!r}")
    if chord in commands:
        found.append(f"command {commands[chord]!r}")
    if chord in firstStrokes:
        samples = firstStrokes[chord]
        found.append(f"first stroke of {len(samples)} outlines, e.g. " + ", ".join(samples[:3]))
    return found


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run from the repo root.")
    theory, punctuation, commands = load(THEORY), load(PUNCTUATION_OUT), load(COMMANDS_OUT)
    firstStrokes: dict[str, list[str]] = {}
    for outline in theory:
        if "/" in outline:
            firstStrokes.setdefault(outline.split("/")[0], []).append(outline)
    buttonKey = starboardKeys(KEYS, GEMINI_PR_KEYMAP)
    lapwing = {o: frenchHours(t) for o, t in load(LAPWING_SOURCE).items()}
    sources = [("P", {o: t for o, t in pluvierEntries().items() if t.startswith("{&")}, PLUVIER_GEMINI), ("L", lapwing, GEMINI)]
    rows: list[tuple[str, str, str, list[str]]] = []          # (label, ireland outline, chord, collisions)
    for tag, entries, gemini in sources:
      for outline, translation in entries.items():
        converted = convertOutline(outline, buttonKey, gemini) or []
        label = translation.replace("{^ ^}", "_").replace("{&", "").replace("}", "")
        for strokes in converted:
            chord = renderFinalStrokesToRTFCRE(starboard, strokes)
            found = collisions(chord, theory, punctuation, commands, firstStrokes)
            if not all(pressable(starboard, s) for s in strokes):
                found.append("not pressable")
            rows.append((f"{tag}:{label}", outline, chord, found))
    wanted = sys.argv[1:]
    if wanted:
        for row in rows:
            if row[0].split(':', 1)[1] in wanted or row[0] in wanted or row[2] in wanted or row[1] in wanted:
                print(f"{row[0]:>14}  {row[2]:<14} {'; '.join(row[3]) or 'free'}")
        return
    bad = [r for r in rows if r[3]]
    print(f"{len(rows)} number chords (P = Pluvier bar, L = Lapwing; `_` = glued with a space), {len(rows) - len(bad)} free, {len(bad)} collide:")
    for kind, test in (("word", lambda c: c.startswith("word")), ("punctuation", lambda c: c.startswith("punct")),
                       ("command", lambda c: c.startswith("command")),
                       ("first stroke", lambda c: c.startswith("first stroke")), ("not pressable", lambda c: c == "not pressable")):
        print(f"  {kind}: {sum(any(test(c) for c in r[3]) for r in bad)}")
    print()
    for digits, _, chord, found in sorted(bad, key=lambda r: (r[0][0], len(r[0]), r[0])):
        print(f"{digits:>14}  {chord:<14} {'; '.join(found)}")


if __name__ == "__main__":
    main()
