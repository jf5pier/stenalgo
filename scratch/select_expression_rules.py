"""Phase 2 Stage A driver: run the proxy selection over the real candidate
pool (scratch/expr_candidates.tsv) and write scratch/expr-rules-proxy.tsv.

Particle set for attach-run generation: every pool unit whose primary Word's
gramCat is a function-word category (PRE, ART:*, PRO:per/rel/ind/dem, CON,
ADV) or an elision unit — printed for vetting.

Usage: env/bin/python scratch/select_expression_rules.py [budget]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.build_expr_candidates import resolveTerm  # noqa: E402
from src.affixes import SimContext  # noqa: E402
from src.expressionrules import (EXPR_RULE_BUDGET, PoolExpression,  # noqa: E402
                                 attachCandidates, briefCandidates,
                                 selectExpressionRules)
from src.expressions import Token  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from src.word import GramCat, Word  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402

CANDIDATES_TSV = REPO / "scratch" / "expr_candidates.tsv"
OUT_TSV = REPO / "scratch" / "expr-rules-proxy.tsv"

FUNCTION_CATS = {
    GramCat.PRE, GramCat["ART:def"], GramCat["ART:ind"],
    GramCat["PRO:per"], GramCat["PRO:rel"], GramCat["PRO:ind"],
    GramCat["PRO:dem"], GramCat.CON, GramCat.ADV,
}


def main() -> None:
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else EXPR_RULE_BUDGET

    starboard = Starboard.fromJSONFile("starboard3h.json")
    assert starboard is not None
    theory = loadDisambiguatedTheory(starboard)
    byOrtho: dict[str, list[Word]] = {}
    for w in theory:
        byOrtho.setdefault(w.ortho, []).append(w)
    ctx = SimContext(starboard, [])  # proxy stage: no outline index needed

    pool: list[PoolExpression] = []
    with open(CANDIDATES_TSV, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        rows = [dict(zip(header, line.rstrip("\n").split("\t"))) for line in fh]
    for row in rows:
        units = [p.split("=")[0] for p in row["phonologies"].split(",") if p]
        tokens = []
        for unit in units:
            pairs = resolveTerm(unit, byOrtho)
            if any(w is None for _, w in pairs):
                tokens = []
                break
            strokes = theory[pairs[0][1]][0]
            tokens.append(Token(unit, strokes))
        if not tokens:
            continue  # dropped rows are logged by build_expr_candidates
        pool.append(PoolExpression(tuple(units), float(row["freq"]), tuple(tokens)))
    print(f"pool: {len(pool)} expressions with resolved tokens")

    particles: frozenset[str] = frozenset()
    seen: dict[str, bool] = {}
    for expr in pool:
        for unit in expr.units:
            if unit in seen:
                continue
            pairs = resolveTerm(unit, byOrtho)
            seen[unit] = bool(pairs and pairs[0][1] is not None
                              and pairs[0][1].gramCat in FUNCTION_CATS)
    particles = frozenset(u for u, ok in seen.items() if ok)
    print(f"particles ({len(particles)}): {' '.join(sorted(particles))}")

    # Q2 families: the lemma of a run's first unit groups its variants
    # (de / d' / de la / de l' / du / des -> "de").
    lemmaOf: dict[str, str] = {}
    for unit, ok in seen.items():
        pairs = resolveTerm(unit, byOrtho)
        if pairs and pairs[0][1] is not None:
            lemmaOf[unit] = pairs[0][1].lemme

    def familyOf(units: tuple[str, ...]) -> str:
        return lemmaOf.get(units[0], "")

    candidates = briefCandidates(pool) + attachCandidates(pool, particles, familyOf)
    families = {c.family for c in candidates if c.family}
    print(f"candidates: {len(candidates)} "
          f"({sum(1 for c in candidates if c.kind == 'brief')} briefs, "
          f"{sum(1 for c in candidates if c.kind == 'attach')} attaches, "
          f"{len(families)} families)")

    result = selectExpressionRules(candidates, pool, budget=budget)

    # Stage B: real keypresses over the real collision index.
    import time

    from src.affixbinding import enumerateKeypresses
    from src.expressionrules import assignKeypresses
    from src.keyboard import canonicalizeStrokes

    realCtx = SimContext(starboard, [])
    realCtx.finalOutlines = {canonicalizeStrokes(s)
                             for alts in theory.values() for s in alts}
    realCtx.singleStrokeOutlines = {o[0] for o in realCtx.finalOutlines
                                    if len(o) == 1}
    t = time.time()
    keypresses = enumerateKeypresses(starboard, realCtx)
    print(f"{len(keypresses)} legal base keypresses ({time.time() - t:.0f}s)")
    t = time.time()
    keypressReport = assignKeypresses(result.selected, pool, realCtx, keypresses,
                                 repairCandidates=200)
    print(f"Stage B assignment done ({time.time() - t:.0f}s)")

    # Stage C: joint repair (cross-family distinctness) + audit, with a
    # feedback round: families implicated in an audit collision lose their
    # base and the repair re-solves (v1 heuristic, up to 3 rounds).
    from src.expressionrules import auditExpressionRules, repairKeypresses
    from src.expressions import Rules, composeOutlineTraced

    chosen: dict = {}
    audit = None
    # Q3 stacking fix: families that co-occur on expressions (joint mass
    # >= 2M) must hold DISJOINT keypresses so both merges can stack on one
    # stroke (ne x pas on a 1-stroke host otherwise keyOverlaps).
    from itertools import combinations

    from src.expressionrules import touchedExpressions as _touched

    famRules: dict[str, list] = {}
    for r in result.selected:
        if r.kind == "attach":
            famRules.setdefault(r.family or " ".join(r.units), []).append(r)
    famTouched = {f: {i for r in rs for i in _touched(r, pool)}
                  for f, rs in famRules.items()}
    disjointPairs = frozenset(
        frozenset((a, b)) for a, b in combinations(sorted(famRules), 2)
        if sum(pool[i].freq for i in famTouched[a] & famTouched[b]) >= 2e6)
    print(f"disjoint-pair constraint on {len(disjointPairs)} co-occurring "
          f"family pairs: {sorted(tuple(sorted(p)) for p in disjointPairs)}")
    for round_ in range(3):
        chosen = repairKeypresses(result.selected, keypressReport,
                                  disjointPairs=disjointPairs)
        audit = auditExpressionRules(result.selected, pool, realCtx)
        print(f"Stage C round {round_}: re-based {len(chosen)} families, "
              f"collisions {len(audit.collisions)}, shadows {len(audit.shadows)}")
        if not audit.collisions:
            break
        poolByUnits = {e.units: e for e in pool}
        rules = Rules(attaches=tuple(
            r.toAttach() for r in result.selected
            if r.kind == "attach" and r.keys is not None))
        banned: set[str] = set()
        progressed = False
        for outline, exprs in audit.collisions.items():
            signatures = []
            for units in exprs:
                traced = composeOutlineTraced(rules, poolByUnits[units].tokens,
                                              realCtx)
                signatures.append({
                    (seg.rule.family, seg.rule.expression)
                    for seg in traced.segments
                    if seg.kind == "attach" and seg.rule is not None
                    and seg.rule.family})
            common = set.intersection(*signatures) if signatures else set()
            differing = set().union(*signatures) - common
            culpritFams = {fam for fam, _units in differing}
            if len(culpritFams) == 1:
                # Selector collapse on a marked host (the host's own * / #
                # swallows the variant's selector — no base can fix it):
                # drop the weaker differing variant; its contexts compose
                # through the common rules instead.
                fam = next(iter(culpritFams))
                unitsSet = {u for _f, u in differing}
                colliding = sorted(
                    (r for r in result.selected
                     if r.family == fam and r.units in unitsSet and r.forms == 0),
                    key=lambda r: -r.freq)
                keep = colliding[0] if len(colliding) > 1 else None
                for drop in colliding:
                    if drop is not keep:
                        result.selected.remove(drop)
                        progressed = True
                continue
            banned.update(culpritFams)
        for family in sorted(banned):
            info = keypressReport.get(family, {})
            alternatives = info.get("alternatives") or []
            remaining = [a for a in alternatives if a[1] != chosen.get(family)]
            if remaining and len(remaining) < len(alternatives):
                info["alternatives"] = remaining
                progressed = True
        if not progressed:
            break

    for family, info in keypressReport.items():
        if family in chosen:
            print(f"  family {family!r}: base={chosen[family]} "
                  f"variants={info['variants']} score={info.get('score', 0):.3e}"
                  + (" (Stage B base kept)" if chosen[family] == info.get("base")
                     else " (moved)"))
        elif info.get("base") is not None:
            print(f"  family {family!r}: base={info['base']} kept from Stage B "
                  f"(repair infeasible or unneeded)")
        else:
            print(f"  family {family!r}: NO LEGAL BASE (variants={info['variants']})")
    assert audit is not None
    share = 100 * audit.savingMass / audit.longformMass if audit.longformMass else 0
    print(f"audit: saving {audit.savingMass:.3e} of {audit.longformMass:.3e} "
          f"longform strokes ({share:.1f}%), exceptions {audit.exceptions}, "
          f"shadows {len(audit.shadows)}, collisions {len(audit.collisions)}")
    for units, outline in audit.shadows[:5]:
        print("  SHADOW", " ".join(units), outline)
    for outline, exprs in list(audit.collisions.items())[:5]:
        print("  COLLISION", outline, [" ".join(u) for u in exprs[:4]])

    with open(OUT_TSV, "w", encoding="utf-8") as out:
        out.write("rank\tkind\tfamily\texpression\tposition\tfreq\t"
                  "strokes_saved\tkeys\tscore\n")
        for rank, rule in enumerate(result.selected, 1):
            keys = ",".join(map(str, rule.keys)) if rule.keys else ""
            out.write(f"{rank}\t{rule.kind}\t{rule.family}\t{' '.join(rule.units)}\t"
                      f"{rule.position}\t{rule.freq:.0f}\t{rule.strokesSaved}\t"
                      f"{keys}\t{rule.score:.3e}\n")

    # Machine-readable dumps for the analyses (Q3 circumfix, Phase 3).
    import json

    finalRules = [
        {"kind": r.kind, "family": r.family, "units": list(r.units),
         "position": r.position, "keys": list(r.keys or ()), "freq": r.freq}
        for r in result.selected]
    with open(REPO / "scratch" / "expr-rules-final.json", "w", encoding="utf-8") as fh:
        json.dump({"rules": finalRules, "chosen": {k: list(v)
                                                   for k, v in chosen.items()}}, fh,
                  ensure_ascii=False, indent=1)
    rulesJoint = Rules(attaches=tuple(
        r.toAttach() for r in result.selected
        if r.kind == "attach" and r.keys is not None))
    with open(REPO / "scratch" / "expr-savings.tsv", "w", encoding="utf-8") as fh:
        fh.write("expr\tfreq\tlongform\tcomposed\tsaving\texceptions\n")
        for expr in pool:
            traced = composeOutlineTraced(rulesJoint, expr.tokens, realCtx)
            fh.write(f"{'+'.join(expr.units)}\t{expr.freq:.0f}\t"
                     f"{expr.longformStrokes}\t{len(traced.strokes or ())}\t"
                     f"{traced.saving}\t{traced.exceptions}\n")
    slots = {(r.family or " ".join(r.units)) if r.kind == "attach"
             else " ".join(r.units) for r in result.selected}
    print(f"selected {len(result.selected)} rules in {len(slots)} slots -> {OUT_TSV}")
    for rank, rule in enumerate(result.selected, 1):
        print(f"  {rank:2}. {rule.kind:6} {' '.join(rule.units):24} "
              f"{rule.position:6} fam={rule.family or '-':6} "
              f"freq={rule.freq:.3e} saved={rule.strokesSaved} "
              f"score={rule.score:.3e}")
    if result.skips:
        print("territory skips:")
        for a, b, ov in result.skips[:10]:
            print(f"  {a!r} skipped vs {b!r} (overlap {ov:.2f})")


if __name__ == "__main__":
    main()
