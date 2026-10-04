"""Item 2b measurement (2026-10-04): how the committed expression rules (scratch/expr-rules-final.json
+ the forced briefs in scratch/expr-briefs.tsv) behave when an attach keypress doubles as a standalone
stroke. Read-only: per attach rule, the pool mass by composition outcome and reason, and chord clashes
against live single-stroke outlines, briefs and other attach chords.

Usage: PYTHONPATH=. env/bin/python scratch/measure_attach_standalone.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.build_expr_candidates import resolveTerm  # noqa: E402
from src.affixes import SimContext  # noqa: E402
from src.expressionrules import ExprRule, PoolExpression, orderBan  # noqa: E402
from src.expressions import (AttachRule, BriefRule, Rules, Token,  # noqa: E402
                             composeOutlineTraced)
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402


def main() -> None:
    starboard = Starboard.fromJSONFile("starboard3h.json")
    assert starboard is not None
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
                         family=r["family"], freq=r["freq"],
                         keys=tuple(r["keys"]) or None,
                         beta=tuple(tuple(s) for s in r["beta"]) or None)
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

    marks = {10, 15}
    tally: dict = defaultdict(lambda: defaultdict(float))
    gainEx: dict = defaultdict(list)
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is None:
            continue
        for seg in traced.segments:
            if seg.kind != "attach" or seg.rule is None:
                continue
            key = (seg.rule.expression, seg.rule.position)
            span = seg.span[1] - seg.span[0]
            label = seg.outcome + (f":{seg.reason}" if seg.reason else "")
            tally[key][label] += expr.freq
            tally[key]["_total"] += expr.freq
            if seg.outcome == "exception" and seg.reason == "noNeighbour":
                n = len([st for t in expr.tokens[seg.span[0]:seg.span[1]] for st in t.strokes])
                if n >= 2:
                    chord = tuple(sorted(seg.rule.keypress))
                    trap = chord in ctx.singleStrokeOutlines
                    tally[key]["_noNbrGain" if not trap else "_noNbrTrap"] += expr.freq * (n - 1)
                    gainEx[key].append((expr.freq * (n - 1), " ".join(expr.units)))
            if seg.outcome == "standalone":
                tally[key]["_standaloneSaved"] += expr.freq * (len(
                    [s for t in expr.tokens[seg.span[0]:seg.span[1]] for s in t.strokes]) - 1)

    briefChords = {s: " ".join(u) for u, s in forced}
    briefChords.update({r.beta[0]: " ".join(r.units) for r in briefRules})
    attachChords: dict = defaultdict(list)
    for r in attachRules:
        attachChords[tuple(sorted(r.keys))].append(" ".join(r.units))

    print("per attach rule: pool mass by outcome (strokes of composed mass are NOT counted here, occurrences are)")
    totals: dict = defaultdict(float)
    for r in sorted(attachRules, key=lambda r: -tally[(r.units, r.position)]["_total"]):
        t = tally[(r.units, r.position)]
        chord = tuple(sorted(r.keys))
        base = tuple(k for k in chord if k not in marks)
        clash = []
        if chord in ctx.singleStrokeOutlines:
            clash.append("LIVE-OUTLINE")
        if chord in briefChords:
            clash.append(f"BRIEF({briefChords[chord]})")
        if base in briefChords:
            clash.append(f"BASE=BRIEF({briefChords[base]})")
        if base != chord and base in ctx.singleStrokeOutlines:
            clash.append("BASE=LIVE-OUTLINE")
        parts = {k: v for k, v in t.items() if not k.startswith("_")}
        for k, v in parts.items():
            totals[k] += v
        total = t["_total"] or 1
        print(f"{' '.join(r.units):12} {r.position[:3]} {chord!s:14} total {t['_total']:.2e}  "
              + "  ".join(f"{k} {100 * v / total:.1f}%" for k, v in sorted(parts.items(), key=lambda kv: -kv[1]))
              + (f"  [{', '.join(clash)}]" if clash else ""))
    grand = sum(totals.values())
    print("\nALL attach segments:", "  ".join(f"{k} {v:.2e} ({100 * v / grand:.1f}%)"
                                                for k, v in sorted(totals.items(), key=lambda kv: -kv[1])))
    print("standalone strokes saved vs longform:",
          f"{sum(t['_standaloneSaved'] for t in tally.values()):.3e}")
    print("\nstandalone-as-fallback potential on noNeighbour exceptions (particle span >= 2 strokes):")
    for k, t in sorted(tally.items(), key=lambda kv: -kv[1]["_noNbrGain"]):
        if t["_noNbrGain"] or t["_noNbrTrap"]:
            top = "; ".join(f"{u} ({g:.1e})" for g, u in sorted(gainEx[k], reverse=True)[:3])
            print(f"  {' '.join(k[0]):10} gain {t['_noNbrGain']:.3e} strokes, blocked by live outline {t['_noNbrTrap']:.3e}   e.g. {top}")
    print(f"  TOTAL gain {sum(t['_noNbrGain'] for t in tally.values()):.3e}, "
          f"blocked {sum(t['_noNbrTrap'] for t in tally.values()):.3e}  (committed attach saving 3.672e9)")
    dup = {c: n for c, n in attachChords.items() if len(n) > 1}
    print("attach chords shared by several rules:", dup or "none")
    print("brief chords equal to an attach chord:",
          {c: (briefChords[c], attachChords[c]) for c in briefChords if c in attachChords} or "none")
    print("brief chords equal to an attach BASE (selector stripped):",
          {c: (briefChords[c], attachChords[b]) for c in briefChords
           for b in attachChords if tuple(k for k in b if k not in marks) == c} or "none")


if __name__ == "__main__":
    main()
