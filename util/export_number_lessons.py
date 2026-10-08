"""
Number Lessons (S10e): the trainer's `chiffres` lesson track, for the two number theories that diverge (Plover English's number bar is
Pluvier's, so there are only two): the Lapwing numpad (`plover_stenalgo_lapwing_numbers.json`) and Pluvier's number bar
(`plover_stenalgo_pluvier_numbers.json`). The trainer has a button of its own for them, apart from the Plover/Pluvier punctuation one.

Run: python -m util.export_number_lessons
Requires the two number dictionaries (`util.export_plover_numbers`), plover_stenalgo_{punctuation,commands,pluvier_punctuation}.json (the glued comma
and point of the punctuation style), starboard3h.json, steno-trainer/public/data/practice-words.json (`util.export_practice_words`) and resources/numberLessons.json (authored:
the lessons, their French texts, the example numbers; `util/number_lessons.py` splits a number into the strokes of a theory).
Output: steno-trainer/public/data/number-lessons.json
    {"tracks": [{"id", "title", "description"}],
     "lessons": {"lapwing": {"plover": [<lesson>, ...], "pluvier": [...]}, "pluvier": {"plover": [...], "pluvier": [...]}},
     "entries": {"lapwing": [<entry>, ...], "pluvier": [<entry>, ...]}}
Same lesson ids in all four sets (the lesson set depends on the number theory and, for the glued comma and point, on the punctuation style). An entry is {"name", "glyph", "family", "primary", "chords", "output", "keywords"} (the Definitions page lists every
single-stroke number of the theory, 1023 for the bar).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from src.keyboard import Starboard
from util.export_lessons import numberInFrench
from util.export_punctuation_lessons import KEYBOARD_JSON, PLOVER_FILES, PLUVIER_FILE, checkedOutline, loadChords, loadWords, phraseItem, ruleLines
from util.number_lessons import expandTokens, glueChords, numberEntries

NUMBER_DATA = "resources/numberLessons.json"
NUMBER_FILES = {"lapwing": "plover_stenalgo_lapwing_numbers.json", "pluvier": "plover_stenalgo_pluvier_numbers.json"}
SCHEMES = {"lapwing": "lapwing", "pluvier": "bar"}
OUTPUT_PATH = "steno-trainer/public/data/number-lessons.json"
TRACKS = ({"id": "chiffres", "title": "Chiffres",
           "description": "Les chiffres et les nombres, avec la touche # : le pavé numérique de Lapwing ou la barre numérique de Pluvier (la même que celle de Plover)."},)
GLUES = {"virgule_collee": ("{^},{^}", "la virgule collée", ","), "point_colle": ("{^}.{^}", "le point collé", ".")}


def glueMarks(style: str, chords: dict[str, str], own: set[str]) -> dict[str, dict[str, Any]]:
    """The glued comma and point of a punctuation style, as pseudo marks: the number lessons take them from the punctuation choice
    (Plover `v-l`, `m-k`; Pluvier `-FRBGS`, `-RPBGS`), not from the number theory."""
    marks: dict[str, dict[str, Any]] = {}
    for slug, (translation, name, glyph) in GLUES.items():
        found = sorted((c for c, t in chords.items() if t == translation), key=lambda c: (len(c), c))
        offered = [c for c in found if c in own] or found
        if not offered:
            raise ValueError(f"no chord for {translation!r} in the {style} punctuation")
        marks[slug] = {"slug": slug, "translation": translation, "name": name, "glyph": glyph, "primary": offered[0],
                       "chords": offered, "own": offered}
    return marks


def buildLessons(theory: str, data: dict[str, Any], entries: dict[str, dict[str, Any]], marks: dict[str, dict[str, Any]],
                 words: dict[str, dict[str, Any]], outlines: dict[str, tuple[tuple[int, ...], ...]]) -> list[dict[str, Any]]:
    """The `chiffres` lessons of one theory: `entries` are its number strokes (`numberEntries`), `marks` the glued comma and point."""
    lessons: list[dict[str, Any]] = []
    everything = {**marks, **entries}
    for index, family in enumerate(data["families"], start=1):
        drill: list[dict[str, Any]] = []
        used: set[str] = set()
        usedOrder: list[str] = []
        for example in family["examples"]:
            tokens = expandTokens(SCHEMES[theory], example, entries)
            used.update(t[1:] for t in tokens if t.startswith("@"))
            usedOrder += [t[1:] for t in tokens if t.startswith("@n_") and t[1:] not in usedOrder]
            item = phraseItem(tokens, everything, words, outlines)
            if item is None:
                raise ValueError(f"the number example {example} has a mark missing in the {theory} theory")
            drill.append(item)
        wanted = [r[1:] if r.startswith("@") else "n_" + r[1:] for r in family["rules"]]
        # the listed strokes the theory has; one with none of them (the bar has no stroke for 10, 100 ...) lists the strokes its examples use
        ruled = [everything[slug] for slug in wanted if slug in everything] \
            or ([everything[slug] for slug in usedOrder if len(slug) > 3][:12] if wanted else [])
        rules = [family["intro"][theory], *ruleLines(ruled, others=True)]
        chords = sorted({tuple(s) for slug in used | {e["slug"] for e in ruled} for s in outlines[everything[slug]["primary"]]
                         if len(s) >= 2})
        lessons.append({
            "id": f"chiffres-{index:02d}", "track": "chiffres", "index": index, "sectionTitle": family["section"],
            "title": f"Leçon {numberInFrench(index)} : {family['title']}", "kind": "chiffres",
            "newKeys": [], "newChords": [list(c) for c in chords],
            "rules": [{"kind": "chiffres", "text": t} for t in rules], "words": drill})
    return lessons


def build(data: dict[str, Any], numberChords: dict[str, dict[str, str]], plover: dict[str, str], pluvier: dict[str, str],
          words: dict[str, dict[str, Any]], starboard: Starboard, keys: tuple[str, ...]) -> dict[str, Any]:
    """`plover` and `pluvier` are the two punctuation styles' chords (`export_punctuation_lessons`): lesson sets exist per number theory
    AND per punctuation style, because the glued comma and point are the punctuation's."""
    ploverOwn = set(plover)
    punctuation = {"plover": (plover, ploverOwn), "pluvier": (pluvier, {c for c, t in pluvier.items() if plover.get(c) != t})}
    lessons: dict[str, dict[str, list[dict[str, Any]]]] = {}
    entriesDoc: dict[str, list[dict[str, Any]]] = {}
    for theory, chords in numberChords.items():
        entries = numberEntries(glueChords(chords))
        lessons[theory] = {}
        for style, (styleChords, own) in punctuation.items():
            marks = glueMarks(style, styleChords, own)
            outlines = {c: checkedOutline(c, keys, starboard) for e in [*entries.values(), *marks.values()] for c in e["chords"]}
            lessons[theory][style] = buildLessons(theory, data, entries, marks, words, outlines)
        entriesDoc[theory] = [{"name": n["name"], "glyph": n["glyph"], "family": "chiffres", "primary": n["primary"],
                               "chords": n["chords"], "output": n["output"], "keywords": n["keywords"]} for n in entries.values()]
    ids = {(theory, style): [lesson["id"] for lesson in value] for theory, styles in lessons.items() for style, value in styles.items()}
    if len({tuple(v) for v in ids.values()}) != 1:
        raise ValueError(f"the number lesson sets have different lessons: {ids}")
    return {"tracks": list(TRACKS), "lessons": lessons, "entries": entriesDoc}


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    with open(NUMBER_DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    numberChords = {theory: loadChords((file,)) for theory, file in NUMBER_FILES.items()}
    document = build(data, numberChords, loadChords(PLOVER_FILES), loadChords((PLUVIER_FILE,)), loadWords(), starboard, KEYS)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(document, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for theory, styles in document["lessons"].items():
        lessons = styles["plover"]
        print(f"{theory}: {len(lessons)} lessons, {sum(len(l['words']) for l in lessons)} drill items, "
              f"{len(document['entries'][theory])} entries")


if __name__ == "__main__":
    main()
