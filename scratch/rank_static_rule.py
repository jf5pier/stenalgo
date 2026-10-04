"""Do we need unit probabilities? Over the open set of scratch/rank_check.py (every single-unit attach rule x every
one-stroke host the composer merges, weighted by rule frequency x host share), compare the winning reading of the
ranker (class order, then probability for unattested readings) with static tie-breaks that need no probability.
Prints: how often more than one unattested reading competes, how often each static rule picks another winner,
and how few (chord -> winner) exceptions cover the disagreement mass.
Usage: PYTHONPATH=. env/bin/python scratch/rank_static_rule.py"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import loadAll  # noqa: E402
from src.expressiondecoder import ExpressionDecoder  # noqa: E402
from src.expressionranking import (ReadingRanker, _kind, attestedTable, composedReading,  # noqa: E402
                                   normalizedSignature, unitProbabilities)
from src.expressions import MERGED, Token, composeOutlineTraced, conflictsOf  # noqa: E402
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


def words(sig: tuple) -> int:
    n = 0
    for p in sig:
        n += len(p[1]) + sum(len(r[0]) for rs in p[3:] for r in rs)
    return n


STATIC = {
    "fewest words, then pieces": lambda sig: (words(sig), len(sig), sig),
    "fewest pieces, then words": lambda sig: (len(sig), words(sig), sig),
    "fewest pieces, then merges last": lambda sig: (len(sig), words(sig), sum(1 for p in sig if p[0] != "content"), sig),
    "most merged attaches first": lambda sig: (-sum(len(p[3]) + len(p[4]) for p in sig), words(sig), sig),
}


def main() -> None:
    ctx, rules, pool, words_, unitStrokes = loadAll()
    dec = ExpressionDecoder(rules, words_, unitStrokes, ctx.isLegal, conflictsOf(ctx))
    data = json.load(open(REPO / "scratch" / "expr-rules-final.json", encoding="utf-8"))
    ruleMass = {(tuple(r["units"]), r["position"]): r["freq"] for r in data["rules"] if r["kind"] == "attach"}
    starboard = Starboard.fromJSONFile("starboard3h.json")
    theory = loadDisambiguatedTheory(starboard)
    probabilities = unitProbabilities((w.ortho, w.frequency) for w in theory)
    entries = []
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is not None:
            entries.append((traced.strokes, composedReading(rules, expr.tokens, traced), expr.freq))
    ranker = ReadingRanker(attestedTable(entries), probabilities)
    ordered = sorted(probabilities, key=probabilities.get, reverse=True)
    floor = probabilities[ordered[-1]]
    TOP = (200, 1000, 5000, 20000)
    truncated = {n: ReadingRanker(attestedTable(entries), {w: probabilities[w] for w in ordered[:n]}) for n in TOP}
    truncDiff = {n: 0.0 for n in TOP}

    hostWeight: dict = defaultdict(float)
    hostToken: dict = {}
    grand = 0.0
    for w, alts in theory.items():
        grand += w.frequency
        out = canonicalizeStrokes(alts[0])
        hostWeight[out] += w.frequency
        if out not in hostToken or w.frequency > hostToken[out][1]:
            hostToken[out] = (Token(w.ortho, out), w.frequency)
    particle: dict = {}
    for expr in pool:
        for t in expr.tokens:
            particle.setdefault(t.unit, t)

    total = 0.0
    contested = 0.0                      # a probability-decided choice: >= 2 readings of class 3 at the top
    disagree: dict = {name: 0.0 for name in STATIC}
    intended: Counter = Counter()        # winner == the composed merge
    exceptions: dict = {name: [] for name in STATIC}
    for rule in rules.attaches:
        if len(rule.expression) != 1 or rule.expression[0] not in particle:
            continue
        pToken = particle[rule.expression[0]]
        mass = ruleMass.get((rule.expression, rule.position), 0.0)
        for out, (hToken, _f) in hostToken.items():
            if len(out) != 1:
                continue
            tokens = (pToken, hToken) if rule.position == "prefix" else (hToken, pToken)
            traced = composeOutlineTraced(rules, tokens, ctx)
            if traced.strokes is None or not any(s.outcome == MERGED for s in traced.segments):
                continue
            sig = composedReading(rules, tokens, traced)
            readings = dec.decode(traced.strokes)
            sigs = [normalizedSignature(tuple(p.signature() for p in r)) for r in readings]
            weight = mass * hostWeight[out] / grand
            total += weight
            best = min(sigs, key=lambda s: ranker.key(canonicalizeStrokes(traced.strokes), s))
            top = min(ranker.key(canonicalizeStrokes(traced.strokes), s)[0] for s in sigs)
            if top == 3 and sum(1 for s in sigs if _kind(s) == 3) > 1:
                contested += weight
                intended["ranker"] += weight * (best == sig)
                for n, tr in truncated.items():
                    o = canonicalizeStrokes(traced.strokes)
                    if min(sigs, key=lambda s: tr.key(o, s)) != best:
                        truncDiff[n] += weight
                for name, f in STATIC.items():
                    pick = min((s for s in sigs if _kind(s) == 3), key=f)
                    intended[name] += weight * (pick == sig)
                    if pick != best:
                        disagree[name] += weight
                        exceptions[name].append((weight, rule.expression[0], hToken.unit))
    print(f"open set weight {total:.3e}; probability-decided (>= 2 unattested readings on top): "
          f"{100 * contested / total:.2f}% of it")
    print(f"winner is the composed merge: ranker {100 * intended['ranker'] / contested:.1f}% of the contested mass")
    for n in TOP:
        print(f"probabilities cut to the {n} most frequent words (rest = 1e-12): other winner on "
              f"{100 * truncDiff[n] / contested:.2f}% of the contested mass")
    for name in STATIC:
        ex = sorted(exceptions[name], reverse=True)
        cum, covered = 0.0, {}
        for i, (w, *_r) in enumerate(ex, 1):
            cum += w
            for target in (0.5, 0.9, 0.99):
                if target not in covered and cum >= target * disagree[name]:
                    covered[target] = i
        print(f"\n{name}: differs from the ranker on {100 * disagree[name] / contested:.1f}% of the contested mass "
              f"({len(ex)} chords); picks the composed merge {100 * intended[name] / contested:.1f}%")
        print(f"   exceptions needed to match the ranker on 50/90/99% of that mass: "
              f"{covered.get(0.5)}/{covered.get(0.9)}/{covered.get(0.99)}")
        for w, r, h in ex[:5]:
            print(f"     {w:.2e} {r} + {h}")


if __name__ == "__main__":
    main()
