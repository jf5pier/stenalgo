"""
The reserved chords of the merged feature keys (docs/MERGED_FEATURE_KEYS_PLAN.md, D8 and D16): every outline of the
other shipped dictionaries, computed from their sources and the layout, never from the shipped JSONs (those are
built after the theory, from it). A merged outline gives way to every one of them.

  punctuation, commands       resources/outlineClassification.tsv converted key to key, plus the phonetic aliases
                              (util.export_plover_complements.build with no theory to filter against)
  pluvier punctuation         the Pluvier chords (buildPluvier, same)
  pluvier / lapwing numbers   the number-bar subsets and resources/reference/lapwing-numbers.json (convertEntries, same)
  spelling                    the letter strokes (util.export_plover_spelling.strokes)
  brief                       the pinned briefs, briefs.json: every chord, and with a theory the one-stroke outlines the
                              word briefs give their family forms (util._briefpins.pinnedChords)
  expression attach           the attach keypresses of the committed rule set, scratch/expr-rules-final.json, as a
                              stroke of their own (a standalone keypress decodes as its particle)
  attested expression         with a theory: the outline of every pool expression (scratch/expr_candidates.tsv)
                              composed on that theory before the merge (D22), the expressions the decoder ranks first

A chord the theory already takes today is still listed: the exporters drop it as before, a merge just cannot take a
new one.
"""
import json
from collections.abc import Iterable

from src.expressions import composeOutlineTraced
from src.keyboard import Starboard, Strokes, canonicalizeStrokes
from src.word import Word
from util._briefpins import pinnedChords
from util._expressioninput import loadExpressionInputs
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

EXPRESSION_RULES = "scratch/expr-rules-final.json"


def attachKeypressesOf(rulesPath: str = EXPRESSION_RULES) -> set[tuple[int, ...]]:
    """The keypress of every attach rule of the committed expression rule set."""
    with open(rulesPath, encoding="utf-8") as f:
        rules = json.load(f)["rules"]
    return {tuple(sorted(rule["keys"])) for rule in rules if rule["kind"] == "attach" and rule["keys"]}


def attestedExpressionOutlines(theory: dict[Word, list[Strokes]], pinned: bool = True) -> set[Strokes]:
    """The canonical outline of every pool expression the committed rules (and, with `pinned`, the pinned expression briefs)
    compose on `theory`."""
    ctx, rules, pool, _words, _unitStrokes = loadExpressionInputs(theory, pinned)
    outlines: set[Strokes] = set()
    for expression in pool:
        traced = composeOutlineTraced(rules, expression.tokens, ctx)
        if traced.strokes is not None:
            outlines.add(canonicalizeStrokes(traced.strokes))
    return outlines


def reservedChords(starboard: Starboard, theory: dict[Word, list[Strokes]] | None = None,
                   briefs: bool = True) -> dict[str, str]:
    """Outline (RTFCRE) -> the source that reserves it; the first source listed wins a shared chord. With `theory`
    (the disambiguated theory before the merge), the attested expressions' outlines too. `briefs=False` leaves the `brief`
    source out and composes the attested expressions without the pinned briefs (what the brief builder checks against)."""
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
    if briefs:
        add(pinnedChords(starboard, theory), "brief")
    add((renderFinalStrokesToRTFCRE(starboard, (keypress,)) for keypress in sorted(attachKeypressesOf())),
        "expression attach")
    if theory is not None:
        add((renderFinalStrokesToRTFCRE(starboard, outline) for outline in sorted(attestedExpressionOutlines(theory, briefs))),
            "attested expression")
    return reserved
