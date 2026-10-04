"""Ranking-loss measurement (user decision 2026-10-04): with the precedence
  0 plain live words > 1 pure brief > 2 attested pool reading (by frequency) > 3 other merged readings (rule mass, then word)
which composed pool expressions would LOSE their outline to a rival reading (and so fall to longform)?
MODE=static drops class 2.   Usage: PYTHONPATH=. env/bin/python scratch/rank_loss.py"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import expectedReading, loadAll, norm  # noqa: E402
from src.expressiondecoder import ExpressionDecoder  # noqa: E402
from src.expressions import composeOutlineTraced  # noqa: E402

STATIC = os.environ.get("MODE") == "static"


def main() -> None:
    ctx, rules, pool, words, unitStrokes = loadAll()
    dec = ExpressionDecoder(rules, words, unitStrokes, ctx.isLegal)
    data = json.load(open(REPO / "scratch" / "expr-rules-final.json", encoding="utf-8"))
    ruleMass = {(tuple(r["units"]), r["position"]): r["freq"] for r in data["rules"]}
    entries = []
    attested: dict = {}                                  # (outline, sig) -> freq
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is None:
            continue
        sig = norm(expectedReading(rules, expr, traced))
        entries.append((expr, traced, sig))
        attested[(traced.strokes, sig)] = attested.get((traced.strokes, sig), 0) + expr.freq

    def klass(sig: tuple) -> int:
        if all(p[0] == "content" and not p[2] and not p[3] and not p[4] for p in sig):
            return 0
        if all(p[0] == "content" and not p[3] and not p[4] for p in sig):
            return 1
        return 3

    def key(outline, sig: tuple) -> tuple:
        k = klass(sig)
        a = attested.get((outline, sig), 0)
        if k == 3 and a and not STATIC:
            return (2, -a)
        mass = sum(ruleMass.get((e, pos), 0) for p in sig for (e, pos) in (p[3] + p[4] + p[5]))
        return (k, -mass, sig)

    total = lost = 0.0
    nLost = nLayered = 0
    reasons: dict = defaultdict(float)
    top = []
    for expr, traced, sig in entries:
        if traced.saving <= 0 and not traced.segments:
            continue
        layered = klass(sig) != 0
        total += expr.freq * traced.saving
        if not layered:
            continue
        nLayered += 1
        rivals = [norm(tuple(p.signature() for p in r)) for r in dec.decode(traced.strokes)]
        best = min(rivals + [sig], key=lambda s: key(traced.strokes, s))
        if best != sig:
            nLost += 1
            lost += expr.freq * traced.saving
            reasons[f"beaten by class {key(traced.strokes, best)[0]}"] += expr.freq * traced.saving
            top.append((expr.freq * traced.saving, " ".join(expr.units), best))
    print(f"mode {'static (no attestation class)' if STATIC else 'full'}")
    print(f"layered pool expressions {nLayered}, losing {nLost}")
    print(f"saving at stake (composed pool, all) {total:.3e}; lost {lost:.3e} = {100 * lost / total:.2f}%")
    for k, v in sorted(reasons.items()):
        print(f"  {k}: {v:.3e}")
    for f, text, best in sorted(top, reverse=True)[:20]:
        print(f"  {f:.2e} {text!r} loses to {[ (p[1], p[3], p[4]) for p in best ]}")


if __name__ == "__main__":
    main()
