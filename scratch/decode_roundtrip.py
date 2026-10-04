"""Step 2 of PLAN_2026-10-04-expression-decoder.md: compose every pool expression with the committed
rules, decode the stroke tuple, check the composed reading is among the decodings.
Usage: PYTHONPATH=. env/bin/python scratch/decode_roundtrip.py"""

from __future__ import annotations

import json
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.affixes import PREFIX, SimContext  # noqa: E402
from src.expressiondecoder import ExpressionDecoder, Piece  # noqa: E402
from src.expressionranking import composedReading, normalizedSignature  # noqa: E402
from src.expressionrules import ExprRule, PoolExpression, orderBan  # noqa: E402
from src.expressions import (EXCEPTION, MERGED, STANDALONE, BriefRule, Rules, Token,  # noqa: E402
                             composeOutlineTraced, conflictsOf, planStream)
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._expressioninput import loadExpressionInputs  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


loadAll = loadExpressionInputs


def expectedReading(rules: Rules, expr: PoolExpression, traced) -> tuple:
    """The composed reading as a (not yet normalized-twice) signature: see src/expressionranking.py."""
    return composedReading(rules, expr.tokens, traced)


def norm(sig: tuple) -> tuple:
    return normalizedSignature(sig)


def rivalClass(sig: tuple) -> str:
    """What a rival reading is: a plain-word shadow, a brief (+ attaches), or attach-based."""
    kinds = {p[0] for p in sig}
    if kinds == {"content"}:
        if any(p[2] for p in sig):
            return "brief(+attaches)"
        if any(p[3] or p[4] for p in sig):
            return "words+merged attaches"
        return "plain words (shadow)"
    return "involves standalone/cluster"


def main() -> None:
    ctx, rules, pool, words, unitStrokes = loadAll()
    dec = ExpressionDecoder(rules, words, unitStrokes, ctx.isLegal, conflictsOf(ctx))
    mass: Counter = Counter()
    count: Counter = Counter()
    bad: list = []
    amb: Counter = Counter()
    ambN: Counter = Counter()
    rivalMass: Counter = Counter()
    rivalCount: Counter = Counter()
    ambiguous: list = []
    byOutline: dict = defaultdict(list)
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is None:
            continue
        expected = expectedReading(rules, expr, traced)
        readings = dec.decode(traced.strokes)
        sigs = [norm(tuple(p.signature() for p in r)) for r in readings]
        expected = norm(expected)
        if not readings:
            cls = "none"
        elif expected not in sigs:
            cls = "mismatch"
        elif len(readings) == 1:
            cls = "unique"
        else:
            cls = "ambiguous"
        mass[cls] += expr.freq
        count[cls] += 1
        if cls in ("none", "mismatch"):
            bad.append((expr.freq, cls, " ".join(expr.units), traced.strokes, expected, sigs))
        if cls == "ambiguous":
            layered = rivalClass(expected) != "plain words (shadow)"
            amb["layered" if layered else "longform only"] += expr.freq
            ambN["layered" if layered else "longform only"] += 1
            for sg in sigs:
                if sg != expected:
                    k = ("layered | " if layered else "longform | ") + rivalClass(sg)
                    rivalMass[k] += expr.freq
                    rivalCount[k] += 1
            ambiguous.append((expr.freq, " ".join(expr.units), traced.strokes, sigs))
        byOutline[traced.strokes].append(" ".join(expr.units))
    total = sum(mass.values())
    print("pool expressions:", sum(count.values()))
    for cls in ("unique", "ambiguous", "mismatch", "none"):
        print(f"  {cls:10} {count[cls]:5}  mass {mass[cls]:.3e} ({100 * mass[cls] / total:.2f}%)")
    print("ambiguous split (expected reading uses the layer, or is plain longform words):",
          {k: (ambN[k], f"{v:.3e}") for k, v in amb.items()})
    print("\nrival readings of the ambiguous outlines (one count per rival reading):")
    for k, v in rivalMass.most_common():
        print(f"  {k:30} {rivalCount[k]:6} rivals, mass {v:.3e}")
    print("\nnone / mismatch (top 15 by frequency):")
    for f, cls, text, strokes, expected, sigs in sorted(bad, reverse=True)[:15]:
        print(f"  {cls} {f:.2e} {text!r} {strokes}\n     expected {expected}\n     got {sigs}")
    print("\nambiguous (top 15):")
    for f, text, strokes, sigs in sorted(ambiguous, reverse=True)[:15]:
        print(f"  {f:.2e} {text!r} {strokes}")
        for s in sigs:
            print("     ", s)
    dup = {o: t for o, t in byOutline.items() if len(t) > 1}
    print("\ncomposed outlines shared by several pool expressions:", len(dup))
    for o, t in list(dup.items())[:10]:
        print("  ", o, t)


if __name__ == "__main__":
    main()
