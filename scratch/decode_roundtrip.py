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

from scratch.build_expr_candidates import resolveTerm  # noqa: E402
from src.affixes import PREFIX, SimContext  # noqa: E402
from src.expressiondecoder import ExpressionDecoder, Piece  # noqa: E402
from src.expressionranking import composedReading, normalizedSignature  # noqa: E402
from src.expressionrules import ExprRule, PoolExpression, orderBan  # noqa: E402
from src.expressions import (EXCEPTION, MERGED, STANDALONE, BriefRule, Rules, Token,  # noqa: E402
                             composeOutlineTraced, conflictsOf, planStream)
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


def loadAll():
    starboard = Starboard.fromJSONFile("starboard3h.json")
    theory = loadDisambiguatedTheory(starboard)
    byOrtho: dict = {}
    for w in theory:
        byOrtho.setdefault(w.ortho, []).append(w)
    ctx = SimContext(starboard, [])
    ctx.finalOutlines = {canonicalizeStrokes(s) for alts in theory.values() for s in alts}
    ctx.singleStrokeOutlines = {o[0] for o in ctx.finalOutlines if len(o) == 1}
    pool: list[PoolExpression] = []
    with open(REPO / "scratch" / "expr_candidates.tsv", encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            row = dict(zip(header, line.rstrip("\n").split("\t")))
            units = [p.split("=")[0] for p in row["phonologies"].split(",") if p]
            pairs = [resolveTerm(u, byOrtho) for u in units]
            if any(any(w is None for _, w in p) for p in pairs):
                continue
            pool.append(PoolExpression(tuple(units), float(row["freq"]), tuple(
                Token(u, theory[p[0][1]][0]) for u, p in zip(units, pairs))))
    data = json.load(open(REPO / "scratch" / "expr-rules-final.json", encoding="utf-8"))
    selected = [ExprRule(kind=r["kind"], units=tuple(r["units"]), position=r["position"],
                         family=r["family"], freq=r["freq"], keys=tuple(r["keys"]) or None,
                         beta=tuple(tuple(s) for s in r["beta"]) or None,
                         elision=r.get("elision", ""), elisionBase=tuple(r.get("elisionBase", ())))
                for r in data["rules"]]
    forced = []
    with open(REPO / "scratch" / "expr-briefs.tsv", encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            forced.append((tuple(f[0].split()), tuple(int(k) for k in f[3].split(","))))
    attachRules = [r for r in selected if r.kind == "attach" and r.keys]
    briefRules = [r for r in selected if r.kind == "brief" and r.beta]
    rules = Rules(attaches=tuple(r.toAttach() for r in attachRules),
                  briefs=tuple(r.toBrief() for r in briefRules)
                  + tuple(BriefRule(u, (s,)) for u, s in forced),
                  orderBan=orderBan(selected, pool))
    words: dict = defaultdict(set)
    unitStrokes: dict = {}
    for w, alts in theory.items():
        for s in alts:
            words[canonicalizeStrokes(s)].add(w.ortho)
        unitStrokes[w.ortho] = max(unitStrokes.get(w.ortho, 0), len(alts[0]))
    return ctx, rules, pool, words, unitStrokes


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
