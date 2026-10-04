"""Decode-time ranking check (src/expressionranking.py), user decision 2026-10-04.
1. Pool: does the top-ranked reading of every composed pool outline equal the composed reading?
2. Open set: for every single-unit attach rule x every one-stroke theory word the composer merges, what does the
   ranked decoder return? Weighted by rule frequency x host frequency share (the independence estimate used by
   the shadow rate): the merge itself / a plain word / a brief / another merge.
Usage: PYTHONPATH=. env/bin/python scratch/rank_check.py"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import loadAll  # noqa: E402
from src.expressiondecoder import ExpressionDecoder  # noqa: E402
from src.expressionranking import (ReadingRanker, attestedTable, composedReading,  # noqa: E402
                                   normalizedSignature, unitProbabilities)
from src.expressions import MERGED, Token, composeOutlineTraced, conflictsOf  # noqa: E402
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


from src.elision import ELISION_PAIRS  # noqa: E402


def twin(sig):
    """Signature with every elided form replaced by its base form (hostless clusters cannot tell them apart)."""
    if sig is None:
        return None
    fix = lambda rs: tuple(sorted((tuple(ELISION_PAIRS.get(u, u) for u in e), pos) for e, pos in rs))  # noqa: E731
    return tuple((p[0], p[1], p[2], fix(p[3]), fix(p[4]), fix(p[5])) for p in sig)


def spelled(sig):
    """The words a reading spells, order-free (attaches merged into one stroke lose their order), elision twins folded."""
    out = []
    for p in sig:
        out.extend(p[1])
        for rs in p[3:]:
            for e, _pos in rs:
                out.extend(e)
    return tuple(sorted(ELISION_PAIRS.get(u, u).replace("'", "").replace("œ", "oe") for u in out))


def main() -> None:
    ctx, rules, pool, words, unitStrokes = loadAll()
    dec = ExpressionDecoder(rules, words, unitStrokes, ctx.isLegal, conflictsOf(ctx))
    data = json.load(open(REPO / "scratch" / "expr-rules-final.json", encoding="utf-8"))
    ruleMass = {(tuple(r["units"]), r["position"]): r["freq"] for r in data["rules"] if r["kind"] == "attach"}
    probabilities = unitProbabilities(
        (w.ortho, w.frequency) for w in loadDisambiguatedTheory(Starboard.fromJSONFile("starboard3h.json")))
    entries = []
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is not None:
            entries.append((expr, traced, composedReading(rules, expr.tokens, traced)))
    ranker = ReadingRanker(attestedTable((t.strokes, sig, e.freq) for e, t, sig in entries), probabilities)

    # 1. pool
    lost, total = [], 0.0
    for expr, traced, sig in entries:
        readings = dec.decode(traced.strokes)
        best = ranker.rank(traced.strokes, readings)[0] if readings else None
        got = normalizedSignature(tuple(p.signature() for p in best)) if best else None
        total += expr.freq
        if twin(got) != twin(sig):
            lost.append((expr.freq, " ".join(expr.units), got))
    print(f"pool: {len(entries)} outlines, top-ranked reading differs from the composed one for {len(lost)} "
          f"(mass {sum(f for f, *_ in lost):.3e} of {total:.3e})")
    for f, text, got in sorted(lost, reverse=True)[:10]:
        print(f"   {f:.2e} {text!r} -> {got}")

    # 2. open set
    starboard = Starboard.fromJSONFile("starboard3h.json")
    theory = loadDisambiguatedTheory(starboard)
    hostWeight: dict = defaultdict(float)
    hostToken: dict = {}
    grand = 0.0
    for w, alts in theory.items():
        grand += w.frequency
        out = canonicalizeStrokes(alts[0])
        hostWeight[out] += w.frequency
        if out not in hostToken or w.frequency > hostToken[out][1]:
            hostToken[out] = (Token(w.ortho, out), w.frequency)
    particle: dict[str, Token] = {}
    for expr in pool:
        for t in expr.tokens:
            particle.setdefault(t.unit, t)
    outcome: Counter = Counter()
    events: list = []
    n = 0
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
            best = ranker.rank(traced.strokes, readings)[0]
            got = normalizedSignature(tuple(p.signature() for p in best))
            weight = mass * hostWeight[out] / grand
            n += 1
            if got == sig:
                kind = "the merge itself"
            elif spelled(got) == spelled(sig):
                kind = "same words, other grouping"
            elif all(p[0] == "content" and not p[3] and not p[4] and not p[2] for p in got):
                kind = "a plain word"
            elif all(p[0] == "content" and not p[3] and not p[4] for p in got):
                kind = "a brief"
            else:
                kind = "another merge"
            outcome[kind] += weight
            if kind == "another merge":
                events.append((weight, rule.expression[0], hToken.unit, [(p[1], p[3], p[4], p[5]) for p in got]))
    tot = sum(outcome.values())
    print(f"\nopen set: {n} merges of a single-unit attach into a one-stroke word, weighted by rule frequency x host share")
    for k, v in outcome.most_common():
        print(f"   {k:18} {100 * v / tot:6.2f}%  ({v:.3e})")
    print("   largest 'another merge' cases (weight, rule + host -> winner):")
    for w, r, h, got in sorted(events, key=lambda e: -e[0])[:14]:
        print(f"     {w:.2e} {r} + {h} -> {got}")


if __name__ == "__main__":
    main()
