"""
Export the steno-trainer's definition-mode lookup table: every word of the
disambiguated theory, grouped by the base (phonetic-theory) chord it shares with its homophones -- the
words the conjugation marks of Discriminating-Feature Stroke Realization (Realization
Phase) and the star/hash marks of Different-Lemma or Grammatical-Category
Disambiguation (S7) have to tell apart -- each
with its readings, phonology and final chord(s).

Grouping is by physically-realized base chord (`canonicalizeStrokes`), not by
phonology: true homophones always share one, and so do the few near-homophones the
layout folds onto the same keys (e.g. /e/ and /O/ share key 14), which need marks
just the same. Each word's own phonology is exported, so the two are told apart.

Compact positional JSON, since this covers the whole lexicon (not just the drill's
10000 most frequent words):
  {"labels": [label, ...],
   "groups": [[base steno, [[ortho, phonology, frequency, [[steno, label index], ...]], ...]], ...]}
Words within a group are most frequent first; a word's chords are its primary one
first, then a self-homograph's alternates (see `loadDisambiguatedTheory`).

Run: python -m util.export_definitions
Requires the same inputs as `util.export_practice_words`.
"""
import json

from src.keyboard import Starboard, canonicalizeStrokes
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util.export_practice_words import (
    KEYBOARD_JSON, RESOLVED_PRESS_SETS_PATH, buildReadingsByWord, chordsWithReadings,
    formatPhonology, formatReadingsLabel,
)

OUTPUT_PATH = "steno-trainer/public/data/definitions.json"


def _mergeIdenticalRows(words: list[list]) -> list[list]:
    """One row for Words that read identically here -- same spelling, phonology, chords
    and labels, e.g. "est" as VER and as AUX -- keeping the higher frequency."""
    merged: dict[str, list] = {}
    for row in words:
        key = json.dumps([row[0], row[1], row[3]])
        if key not in merged or merged[key][2] < row[2]:
            merged[key] = row
    return list(merged.values())


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")
    theory, disambiguatedTheory = loadPhoneticAndDisambiguatedTheory(starboard)
    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        readingsByWord = buildReadingsByWord(json.load(f), theory)

    labelIndex: dict[str, int] = {}
    wordsByBase: dict[str, list] = {}
    for baseStrokes, words in theory.items():
        base = starboard.strokesToRTFCRE(canonicalizeStrokes(baseStrokes))
        group = wordsByBase.setdefault(base, [])
        for word in words:
            if word not in disambiguatedTheory:
                continue
            chords, _aligned = chordsWithReadings(word, disambiguatedTheory[word], readingsByWord)
            group.append([
                word.ortho, formatPhonology(word), round(word.frequency, 2),
                [[renderFinalStrokesToRTFCRE(starboard, strokes),
                  labelIndex.setdefault(formatReadingsLabel(word.gramCat, readings), len(labelIndex))]
                 for strokes, readings in chords],
            ])

    groups = [
        [base, sorted(_mergeIdenticalRows(words), key=lambda w: (-w[2], w[0]))]
        for base, words in sorted(wordsByBase.items())
        if words
    ]
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"labels": list(labelIndex), "groups": groups}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {OUTPUT_PATH}: {sum(len(g[1]) for g in groups)} words in {len(groups)} base-chord groups,"
          f" {len(labelIndex)} distinct labels.")


if __name__ == "__main__":
    main()
