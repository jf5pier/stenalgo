"""
Hand-run check of the merged feature keys on the built outputs (docs/MERGED_FEATURE_KEYS_PLAN.md, MKD30): the hard
constraints MKH1-MKH4, on the theory as `util._theoryio` loads it (merged when STENALGO_MERGE_FEATURE_KEYS=1) and on the
shipped dictionaries. Exit status 1 when one fails.

  MKH1  no outline of the theory written by two spellings (1990-reform doublets exempted, as everywhere), and no theory
      outline in another shipped dictionary (punctuation, commands, Pluvier punctuation and numbers, Lapwing numbers,
      spelling, affix abbreviations);
  MKH2  every merged stroke pressable;
  MKH3  no merged outline is a reserved chord (util/_reservedchords.py: the other dictionaries' sources, the expression
      briefs and attach keypresses);
  MKH4  no two spellings of one lemmeGramCat share an outline (docs/specs/discriminating-features.md section 5).

Prerequisites: the pickles (or what rebuilds them), starboard3h.json, keypress_groups.json, resolved_press_sets.json,
the plover_stenalgo_*.json files. Run: python -m util.check_merged_feature_keys
"""
import json
import sys
from collections import defaultdict

from src.ambiguitychecker import loadReform1990DoubletPairs
from src.keyboard import Starboard
from src.mergedfeaturekeys import MERGE_FEATURE_KEYS
from util._reservedchords import reservedChords
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util.export_plover_complements import pressable
from util.export_practice_words import RESOLVED_PRESS_SETS_PATH, buildReadingsByWord, chordsWithAlternates

OTHER_DICTIONARIES = ("plover_stenalgo_punctuation.json", "plover_stenalgo_commands.json",
                      "plover_stenalgo_pluvier_punctuation.json", "plover_stenalgo_pluvier_numbers.json",
                      "plover_stenalgo_lapwing_numbers.json", "plover_stenalgo_spelling.json",
                      "plover_stenalgo_affix_dictionary.json")
SHOWN = 10


def main() -> int:
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    if keyboard is None:
        raise RuntimeError("starboard3h.json not found; run from the repo root.")
    phonetic, theory, wordToStrokes, wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(keyboard)
    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        readingsByWord = buildReadingsByWord(json.load(f), phonetic, wordToStrokes=wordToStrokes,
                                             wordsByOrthoLemme=wordsByOrthoLemme)
    doublets = {frozenset(pair) for pair in loadReform1990DoubletPairs()}
    owners: dict[str, set[tuple[str, str]]] = defaultdict(set)
    merged: list[tuple[str, str, tuple[tuple[int, ...], ...]]] = []
    for word, outlines in theory.items():
        for outline in outlines:
            owners[renderFinalStrokesToRTFCRE(keyboard, outline)].add((word.ortho, word.lemmeGramCat))
        chords, _aligned = chordsWithAlternates(word, outlines, readingsByWord)
        merged += [(word.ortho, renderFinalStrokesToRTFCRE(keyboard, strokes), strokes)
                   for strokes, _readings, longs in chords if longs]
    failures: dict[str, list[str]] = {}

    def spellings(outline: str) -> set[str]:
        return {ortho for ortho, _lemme in owners[outline]}
    shared = [o for o in owners if len(spellings(o)) > 1 and frozenset(spellings(o)) not in doublets]
    for path in OTHER_DICTIONARIES:
        with open(path, encoding="utf-8") as f:
            shared += [f"{o} (also in {path})" for o in json.load(f) if o in owners]
    failures["MKH1 outlines shared by two spellings or dictionaries"] = shared
    failures["MKH2 unpressable merged strokes"] = [f"{ortho} {text}" for ortho, text, strokes in merged
                                                if not all(pressable(keyboard, stroke) for stroke in strokes)]
    reserved = reservedChords(keyboard)
    failures["MKH3 merged outlines on a reserved chord"] = [f"{ortho} {text} ({reserved[text]})"
                                                         for ortho, text, _strokes in merged if text in reserved]
    byLemme: list[str] = []
    for steno, pairs in owners.items():
        lemmes: dict[str, set[str]] = defaultdict(set)
        for ortho, lemme in pairs:
            lemmes[lemme].add(ortho)
        byLemme += [f"{steno} {lemme}: {sorted(orthos)}" for lemme, orthos in lemmes.items()
                    if len(orthos) > 1 and frozenset(orthos) not in doublets]
    failures["MKH4 same-lemmeGramCat spellings sharing an outline"] = byLemme

    print(f"merge {'on' if MERGE_FEATURE_KEYS else 'off'}: {len(owners)} theory outlines, {len(merged)} merged")
    for name, found in failures.items():
        print(f"{name}: {len(found)}" + "".join(f"\n  {line}" for line in found[:SHOWN]))
    return 1 if any(failures.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
