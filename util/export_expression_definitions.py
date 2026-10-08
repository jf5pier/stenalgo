"""
Theory Export (S8)-style trainer branch for the Definitions page's expression entries: the **attach words** (the
particles written as an attach keypress on a host: `de`, `la`, `et`, `il`...), the **composed attach words** (an
attach rule over several units, `il y`, `n' y`) and the **composed phrases** that several rules shorten in one
outline (`de la`, `et les`). A lookup of that spelling on the Definitions page shows these next to the dictionary
words (`definitions.json`, untouched).

Run: python -m util.export_expression_definitions
Requires the inputs of util.export_expression_lessons (both pickles, starboard3h.json and the committed expression
files of scratch/). Output: steno-trainer/public/data/expression-definitions.json
    {"attaches": [{"text", "units", "position", "family", "label", "keys", "keyNames", "steno", "phonology",
                   "examples": [{"text", "phonology", "steno", "longform", "label"}, ...]}, ...],
     "phrases":  [{"text", "units", "phonology", "steno", "longform", "label"}, ...]}
`steno` is the outline text of `definitions.json` (parsed back into keys by the trainer); an attach rule's own `steno`
is its keypress alone. The composer is the one the Plover plugin and the lessons use, so a shown outline is what
Plover writes.
"""
from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from typing import Any

from src.affixes import SimContext
from src.expressions import AttachRule, Rules
from src.keyboard import Starboard
from util._expressioninput import CANDIDATES, loadExpressionInputs
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_expression_data import writtenText
from util.export_expression_lessons import (Composed, attachLabel, composeAll, loadPhonologies, rankRules)
from util.export_affix_lessons import _savedText

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "steno-trainer/public/data/expression-definitions.json"

EXAMPLES_PER_ATTACH = 6


def loadUnitPhonologies() -> dict[str, str]:
    """Phonology of each unit (`il`, `n'`...) of the candidate pool, from its `unit=phonology` pairs."""
    out: dict[str, str] = {}
    with open(CANDIDATES, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            for pair in row["phonologies"].split(","):
                unit, _, phonology = pair.partition("=")
                if unit and phonology:
                    out.setdefault(unit, phonology)
    return out


def _render(starboard: Starboard, strokes: Any) -> str:
    return renderFinalStrokesToRTFCRE(starboard, strokes)


def _phraseDoc(item: Composed, starboard: Starboard, phonologies: dict[tuple[str, ...], str]) -> dict[str, Any]:
    assert item.comp.strokes is not None
    return {"text": writtenText(item.expr.units), "units": list(item.expr.units),
            "phonology": phonologies.get(item.expr.units, ""), "steno": _render(starboard, item.comp.strokes),
            "longform": _render(starboard, item.longform), "label": _savedText(item.comp.saving)}


def buildExpressionDefinitions(rules: Rules, pool: Sequence[Any], ctx: SimContext, starboard: Starboard,
                               phonologies: dict[tuple[str, ...], str] | None = None,
                               unitPhonologies: dict[str, str] | None = None) -> dict[str, Any]:
    """Pure builder: the committed rule set and pool -> the `expression-definitions.json` document."""
    phonologies = phonologies or {}
    unitPhonologies = unitPhonologies or {}
    composed = composeAll(rules, pool, ctx)
    _families, attaches, _briefs = rankRules(rules, composed)
    attachTexts = {" ".join(r.expression) for r in attaches}
    attachDocs: list[dict[str, Any]] = []
    for rule in attaches:
        mine = [c for c in composed if rule in c.fired]
        mine.sort(key=lambda c: (len(c.fired), -c.expr.freq, c.expr.units))
        examples = [_phraseDoc(c, starboard, phonologies) for c in mine if c.expr.units != rule.expression
                    ][:EXAMPLES_PER_ATTACH]
        keys = sorted(rule.keypress)
        attachDocs.append({
            "text": " ".join(rule.expression), "units": list(rule.expression), "position": rule.position,
            "family": rule.family, "label": attachLabel(rule, attaches), "keys": keys,
            "keyNames": [starboard.keyDisplayName(k) for k in keys], "steno": _render(starboard, (tuple(keys),)),
            "phonology": ".".join(unitPhonologies.get(u, "") for u in rule.expression), "examples": examples})
    phrases = [_phraseDoc(c, starboard, phonologies) for c in composed
               if len(c.expr.units) >= 2 and writtenText(c.expr.units) not in attachTexts]
    return {"attaches": attachDocs, "phrases": phrases}


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    ctx, rules, pool, _words, _unitStrokes = loadExpressionInputs()
    document = buildExpressionDefinitions(rules, pool, ctx, starboard, loadPhonologies(), loadUnitPhonologies())
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(document['attaches'])} attach rules, {len(document['phrases'])} composed phrases.")


if __name__ == "__main__":
    main()
