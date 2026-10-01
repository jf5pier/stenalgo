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
    with open(OUT_TSV, "w", encoding="utf-8") as out:
        out.write("rank\tkind\tfamily\texpression\tposition\tfreq\t"
                  "strokes_saved\tscore\n")
        for rank, rule in enumerate(result.selected, 1):
            out.write(f"{rank}\t{rule.kind}\t{rule.family}\t{' '.join(rule.units)}\t"
                      f"{rule.position}\t{rule.freq:.0f}\t{rule.strokesSaved}\t"
                      f"{rule.score:.3e}\n")
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
