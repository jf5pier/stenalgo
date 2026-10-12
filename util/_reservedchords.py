"""
The reserved chords of the merged feature keys (docs/MERGED_FEATURE_KEYS_PLAN.md, D8 and D16): every outline of the
other shipped dictionaries, computed from their sources and the layout, never from the shipped JSONs (those are
built after the theory, from it). A merged outline gives way to every one of them.

  punctuation, commands       resources/outlineClassification.tsv converted key to key, plus the phonetic aliases
                              (util.export_plover_complements.build with no theory to filter against)
  pluvier punctuation         the Pluvier chords (buildPluvier, same)
  pluvier / lapwing numbers   the number-bar subsets and resources/reference/lapwing-numbers.json (convertEntries, same)
  spelling                    the letter strokes (util.export_plover_spelling.strokes)
  expression brief            the committed briefs, scratch/expr-briefs.tsv
  expression attach           the attach keypresses of the committed rule set, scratch/expr-rules-final.json, as a
                              stroke of their own (a standalone keypress decodes as its particle)

A chord the theory already takes today is still listed: the exporters drop it as before, a merge just cannot take a
new one.
"""
import csv
import json
from collections.abc import Iterable

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_plover_complements import (
    COMMAND_ALIASES,
    SOURCE_PLUVIER,
    build,
    buildPluvier,
    loadRows,
    phoneticAliases,
)
from util.export_plover_numbers import LAPWING_SOURCE, PLUVIER_GEMINI, convertEntries, pluvierEntries
from util.export_plover_spelling import strokes as spellingStrokes
from util.export_plover_system import GEMINI_PR_LABELS

EXPRESSION_BRIEFS = "scratch/expr-briefs.tsv"
EXPRESSION_RULES = "scratch/expr-rules-final.json"


def attachKeypressesOf(rulesPath: str = EXPRESSION_RULES) -> set[tuple[int, ...]]:
    """The keypress of every attach rule of the committed expression rule set."""
    with open(rulesPath, encoding="utf-8") as f:
        rules = json.load(f)["rules"]
    return {tuple(sorted(rule["keys"])) for rule in rules if rule["kind"] == "attach" and rule["keys"]}


def reservedChords(starboard: Starboard) -> dict[str, str]:
    """Outline (RTFCRE) -> the source that reserves it; the first source listed wins a shared chord."""
    keys = tuple(starboard.keyDisplayNames())
    buttonKey = {label: index for index, label in enumerate(GEMINI_PR_LABELS)}
    reserved: dict[str, str] = {}

    def add(outlines: Iterable[str], source: str) -> None:
        for outline in outlines:
            reserved.setdefault(outline, source)

    complements = build(loadRows(), starboard, buttonKey, set(), set(), phoneticAliases(keys),
                        phoneticAliases(keys, COMMAND_ALIASES))
    add(complements["punctuation"], "punctuation")
    add(complements["commands"], "commands")
    add(buildPluvier(loadRows(sources=(SOURCE_PLUVIER,)), starboard, buttonKey, keys, set(), set())["punctuation"],
        "pluvier punctuation")
    with open(LAPWING_SOURCE, encoding="utf-8") as f:
        lapwing: dict[str, str] = json.load(f)
    add(convertEntries(pluvierEntries(), starboard, buttonKey, set(), set(), set(), PLUVIER_GEMINI)["entries"],
        "pluvier numbers")
    add(convertEntries(lapwing, starboard, buttonKey, set(), set(), set())["entries"], "lapwing numbers")
    add((renderFinalStrokesToRTFCRE(starboard, (stroke,)) for stroke in spellingStrokes()), "spelling")
    with open(EXPRESSION_BRIEFS, encoding="utf-8") as f:
        add((row["rtfcre"] for row in csv.DictReader(f, delimiter="\t")), "expression brief")
    add((renderFinalStrokesToRTFCRE(starboard, (keypress,)) for keypress in sorted(attachKeypressesOf())),
        "expression attach")
    return reserved
