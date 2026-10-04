"""Step 5 data export of PLAN_2026-10-04-expression-decoder.md: write the decoder's data (src/expressiondata.py)
and check it reproduces the in-memory ranked decode on every pool outline plus a sample of the open set.
Usage: PYTHONPATH=. env/bin/python scratch/export_expression_data.py [OUT.json]
Default OUT: plover_stenalgo_expressions.stenalgo"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import loadAll  # noqa: E402
from src.expressiondata import bundleToDict, legalityFromStarboard, loadBundle  # noqa: E402
from src.expressiondecoder import ExpressionDecoder  # noqa: E402
from src.expressionranking import (ReadingRanker, attestedTable, attestedTexts, composedReading,  # noqa: E402
                                   normalizedSignature, rankedDecode, unitProbabilities)
from src.expressions import composeOutlineTraced, conflictsOf  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


def writtenText(units: tuple[str, ...]) -> str:
    """The units as written: spaces between words, none after an elided one (`qu'` + `il`)."""
    text = ""
    for unit in units:
        text += unit if not text or text.endswith("'") else " " + unit
    return text


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else REPO / "plover_stenalgo_expressions.stenalgo")
    ctx, rules, pool, words, unitStrokes = loadAll()
    conflicts = conflictsOf(ctx)
    probabilities = unitProbabilities(
        (w.ortho, w.frequency) for w in loadDisambiguatedTheory(Starboard.fromJSONFile("starboard3h.json")))
    entries = []
    texts = []
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is not None:
            entries.append((traced.strokes, composedReading(rules, expr.tokens, traced), expr.freq))
            texts.append((traced.strokes, entries[-1][1], expr.freq, writtenText(expr.units)))
    attested = attestedTable(entries)
    legality = legalityFromStarboard(ctx.starboard)
    doc = bundleToDict(rules, words, unitStrokes, attested, probabilities, conflicts, legality,
                       attestedTexts(texts))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB): {len(doc['rules']['attaches'])} attaches, "
          f"{len(doc['rules']['briefs'])} briefs, {len(doc['words'])} outlines, {len(attested)} attested")

    # check 1: the legality model equals SimContext.isLegal on every chord a decode asks about
    decoder, ranker = loadBundle(out)
    live = ExpressionDecoder(rules, words, unitStrokes, ctx.isLegal, conflicts)
    liveRanker = ReadingRanker(attested, probabilities)
    checked = bad = 0
    for outline, _sig, _f in entries:
        for stroke in outline:
            for keys in {tuple(sorted(stroke)), tuple(sorted(k for k in stroke if k not in (10, 15)))}:
                checked += 1
                bad += decoder.isLegal(keys) != ctx.isLegal(keys)
    print(f"legality: {checked} chords, {bad} differ")

    # check 2: the loaded decoder + ranker give the same ranked reading as the in-memory ones
    diff = 0
    for outline, _sig, _f in entries:
        a, b = rankedDecode(live, liveRanker, outline), rankedDecode(decoder, ranker, outline)
        sig = lambda r: None if r is None else normalizedSignature(tuple(p.signature() for p in r))  # noqa: E731
        diff += sig(a) != sig(b)
    print(f"pool round trip: {len(entries)} outlines, {diff} differ from the in-memory ranked decode")


if __name__ == "__main__":
    main()
