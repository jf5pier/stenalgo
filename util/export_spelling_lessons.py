"""
Spelling Lessons (S10f): the trainer's `epellation` lesson track, for the spelling theory of `util/export_plover_spelling.py`
(one theory: no style switch). The authored lessons (`resources/spellingLessons.json`: titles, French texts, the example words) are
built into drill items by `util/export_punctuation_lessons.phraseItem`: an example is a word or a short phrase spelled letter by
letter, one stroke per letter (`Paris` is five strokes, an upper-case letter takes the UPPER ending, a space in the example is the
ending that is followed by a space: `S N C F`).

Run: python -m util.export_spelling_lessons
Requires plover_stenalgo_spelling.json (`util.export_plover_spelling`), starboard3h.json and resources/spellingLessons.json.
Output: steno-trainer/public/data/spelling-lessons.json
    {"tracks": [{"id", "title", "description"}], "lessons": [<lesson>, ...], "entries": [<entry>, ...]}
An entry (the Definitions page) is {"name", "glyph", "family", "primary", "chords", "output", "keywords"}: one per character and ending (156).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_lessons import numberInFrench
from util.export_plover_spelling import ENDINGS, SPELLING_OUT, letterChords, strokes, translation
from util.export_punctuation_lessons import KEYBOARD_JSON, checkedOutline, phraseItem

SPELLING_DATA = "resources/spellingLessons.json"
OUTPUT_PATH = "steno-trainer/public/data/spelling-lessons.json"
TRACKS = ({"id": "epellation", "title": "Épellation",
           "description": "Les lettres une à une, avec leurs accents, la majuscule et l'espace : pour les noms, les sigles et tout ce qui n'est pas dans le dictionnaire."},)
ENDING_NAMES = {"lower": "minuscule", "upper": "majuscule", "lowerSpace": "minuscule suivie d'une espace",
                "upperSpace": "majuscule suivie d'une espace"}


def slugOf(char: str, ending: str) -> str:
    return f"{char.lower()}_{ending}"


def entriesOf(starboard: Starboard) -> dict[str, dict[str, Any]]:
    """The 156 pseudo marks: slug `<char>_<ending>`, one chord each."""
    bySlug: dict[str, dict[str, Any]] = {}
    for char, keys in letterChords().items():
        for ending, endingKeys in ENDINGS.items():
            chord = renderFinalStrokesToRTFCRE(starboard, (tuple(sorted(set(keys) | set(endingKeys))),))
            shown = char.upper() if ending.startswith("upper") else char
            spaced = ending.endswith("Space")
            bySlug[slugOf(char, ending)] = {
                "slug": slugOf(char, ending), "translation": translation(char, ending),
                "name": f"la lettre {shown} ({ENDING_NAMES[ending]})", "family": "epellation",
                "glyph": shown + ("␣" if spaced else ""), "keywords": ["lettre", "épellation"],
                "primary": chord, "chords": [chord], "own": [chord], "output": shown + ("␣" if spaced else "")}
    return bySlug


def spell(example: str) -> list[str]:
    """The marks of an example: one per letter, the ending that is followed by a space where the example has a space."""
    tokens: list[str] = []
    pending: list[tuple[str, bool]] = []
    for char in example:
        if char == " ":
            if not pending:
                raise ValueError(f"misplaced space in the spelling example {example!r}")
            pending[-1] = (pending[-1][0], True)
        elif char.lower() in letterChords():
            pending.append((char, False))
        else:
            raise ValueError(f"the spelling example {example!r} holds {char!r}, which has no chord")
    if pending and example.endswith(" "):
        raise ValueError(f"the spelling example {example!r} ends with a space")
    for char, spaced in pending:
        ending = ("upper" if char != char.lower() else "lower") + ("Space" if spaced else "")
        tokens.append("@" + slugOf(char, ending))
    return tokens


def buildLessons(data: dict[str, Any], bySlug: dict[str, dict[str, Any]], outlines: dict[str, tuple[tuple[int, ...], ...]],
                 starboard: Starboard) -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []
    parts = letterChords()
    for index, family in enumerate(data["families"], start=1):
        drill = []
        used: set[tuple[int, ...]] = set()
        for example in family["examples"]:
            tokens = spell(example)
            item = phraseItem(tokens, bySlug, {}, outlines, capitalizeFirst=False)
            if item is None:
                raise ValueError(f"spelling example {example!r}: a letter is missing")
            drill.append(item)
            used.update(tuple(s) for token in tokens for s in outlines[bySlug[token[1:]]["primary"]] if len(s) >= 2)
        rules = [family["intro"]]
        for char in family["letters"]:
            chord = renderFinalStrokesToRTFCRE(starboard, (tuple(sorted(parts[char])),))
            rules.append(f"{char.upper()} ( {char} ) : {chord}, puis la terminaison de la main droite.")
        lessons.append({
            "id": f"epellation-{index:02d}", "track": "epellation", "index": index, "sectionTitle": family["section"],
            "title": f"Leçon {numberInFrench(index)} : {family['title']}", "kind": "epellation",
            "newKeys": [], "newChords": [list(c) for c in sorted(used)],
            "rules": [{"kind": "epellation", "text": t} for t in rules], "words": drill})
    return lessons


def build(data: dict[str, Any], dictionary: dict[str, str], starboard: Starboard, keys: tuple[str, ...]) -> dict[str, Any]:
    bySlug = entriesOf(starboard)
    expected = {chord: text for chord, text in ((renderFinalStrokesToRTFCRE(starboard, (s,)), t) for s, t in strokes().items())}
    if expected != dictionary:
        raise ValueError(f"{SPELLING_OUT} is not what util.export_plover_spelling would write now: rerun it")
    outlines = {e["primary"]: checkedOutline(e["primary"], keys, starboard) for e in bySlug.values()}
    entries = [{k: e[k] for k in ("name", "glyph", "family", "primary", "chords", "output", "keywords")} for e in bySlug.values()]
    return {"tracks": list(TRACKS), "lessons": buildLessons(data, bySlug, outlines, starboard), "entries": entries}


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    with open(SPELLING_DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(SPELLING_OUT, encoding="utf-8") as fh:
        dictionary = json.load(fh)
    document = build(data, dictionary, starboard, KEYS)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(document, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    lessons = document["lessons"]
    print(f"{len(lessons)} lessons, {sum(len(lesson['words']) for lesson in lessons)} drill items, {len(document['entries'])} entries")


if __name__ == "__main__":
    main()
