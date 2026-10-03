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

    # Q2 families, refined 2026-10-02: the lemma of a run's first unit
    # groups its variants (de / d' / de la / de l' / du / des -> "de");
    # que/qu' runs group by the FOLLOWING word's category instead — three
    # determiner subfamilies, the subject pronouns, and the bare head
    # ("que and qu' before any other words").
    lemmaOf: dict[str, str] = {}
    for unit, ok in seen.items():
        pairs = resolveTerm(unit, byOrtho)
        if pairs and pairs[0][1] is not None:
            lemmaOf[unit] = pairs[0][1].lemme

    QUE_HEADS = frozenset({"que", "qu'"})
    QUE_DEFINITE = frozenset({"le", "la", "l'", "les"})
    QUE_INDEFINITE = frozenset({"un", "une", "des", "du"})
    QUE_DEMONSTRATIVE = frozenset({"ce", "cet", "cette", "ces"})
    QUE_PRONOUNS = frozenset({"je", "j'", "tu", "il", "elle", "on",
                              "nous", "vous", "ils", "elles"})

    def queFamilyOf(units: tuple[str, ...]) -> str:
        """The que-domain cut (user decision 2026-10-02): the determiner
        subfamilies, the subject-pronoun family, and the bare head. Empty
        outside the que domain."""
        if units[0] in QUE_HEADS:
            if len(units) >= 2:
                second = units[1]
                if second in QUE_DEFINITE:
                    return "que+def"
                if second in QUE_INDEFINITE:
                    return "que+indef"
                if second in QUE_DEMONSTRATIVE:
                    return "que+dem"
                if second in QUE_PRONOUNS:
                    return "que+pron"
            return "que"
        return ""

    def familyOf(units: tuple[str, ...]) -> str:
        return queFamilyOf(units) or lemmaOf.get(units[0], "")

    candidates = briefCandidates(pool, familyOf=queFamilyOf) \
        + attachCandidates(pool, particles, familyOf)
    # The pronoun family differentiates by briefs, never by a merged
    # keypress or a */# selector (user decision 2026-10-02): it gets no
    # attach candidates at all.
    candidates = [c for c in candidates
                  if not (c.kind == "attach" and c.family == "que+pron")]
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

    # Stage B for the selected BRIEF rules (2026-10-02: the que families'
    # briefs win slots in the same greedy as the attaches): derived strokes
    # in descending-frequency order over one shared taken set.
    from src.expressionrules import assignBriefStrokes, deriveBriefStroke
    t = time.time()
    briefReport = assignBriefStrokes(result.selected, pool, realCtx,
                                     freeChords=keypresses)
    failedBriefs = sorted(u for u, got in briefReport.items() if got is None)
    if failedBriefs:
        print(f"{len(failedBriefs)} brief rules got no stroke (dropped): "
              + "; ".join(" ".join(u) for u in failedBriefs))
        result.selected = [r for r in result.selected
                           if r.kind != "brief" or r.beta is not None]
    print(f"brief strokes: {sum(1 for v in briefReport.values() if v)} derived "
          f"({time.time() - t:.0f}s)")
    # every stroke a selected brief now holds — re-derivations and the
    # forced-brief section must not take it again
    selBriefTaken = {r.beta[0] for r in result.selected
                     if r.kind == "brief" and r.beta is not None}

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
        rules = Rules(
            attaches=tuple(r.toAttach() for r in result.selected
                           if r.kind == "attach" and r.keys is not None),
            briefs=tuple(r.toBrief() for r in result.selected
                         if r.kind == "brief" and r.beta is not None))
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
                    if seg.kind in ("attach", "brief") and seg.rule is not None
                    and seg.rule.family})
            common = set.intersection(*signatures) if signatures else set()
            differing = set().union(*signatures) - common
            culpritFams = {fam for fam, _units in differing}
            if len(culpritFams) == 1:
                fam = next(iter(culpritFams))
                if any(r.family == fam and r.kind == "brief"
                       for r in result.selected):
                    # a BRIEF family's stroke collides: re-derive every
                    # family brief with the colliding outline (and each
                    # brief's own stroke) in the taken set
                    famRules = [r for r in result.selected
                                if r.kind == "brief" and r.family == fam
                                and r.beta is not None]
                    for r in famRules:
                        selBriefTaken.add(r.beta[0])   # force a move
                    for r in famRules:
                        got = deriveBriefStroke(poolByUnits[r.units], realCtx,
                                                selBriefTaken,
                                                freeChords=keypresses)
                        if got is None:
                            result.selected.remove(r)
                        else:
                            r.beta = (got[0],)
                            selBriefTaken.add(got[0])
                    progressed = True
                    continue
                # Selector collapse on a marked host (the host's own * / #
                # swallows the variant's selector — no base can fix it):
                # drop the weaker differing variant; its contexts compose
                # through the common rules instead.
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
            if rule.beta:
                keys = "/".join(",".join(map(str, st)) for st in rule.beta)
            out.write(f"{rank}\t{rule.kind}\t{rule.family}\t{' '.join(rule.units)}\t"
                      f"{rule.position}\t{rule.freq:.0f}\t{rule.strokesSaved}\t"
                      f"{keys}\t{rule.score:.3e}\n")

    # Machine-readable dumps for the analyses (Q3 circumfix, Phase 3).
    import json

    finalRules = [
        {"kind": r.kind, "family": r.family, "units": list(r.units),
         "position": r.position, "keys": list(r.keys or ()),
         "beta": [list(st) for st in (r.beta or ())], "freq": r.freq}
        for r in result.selected]
    with open(REPO / "scratch" / "expr-rules-final.json", "w", encoding="utf-8") as fh:
        json.dump({"rules": finalRules, "chosen": {k: list(v)
                                                   for k, v in chosen.items()}}, fh,
                  ensure_ascii=False, indent=1)
    rulesJoint = Rules(
        attaches=tuple(r.toAttach() for r in result.selected
                       if r.kind == "attach" and r.keys is not None),
        briefs=tuple(r.toBrief() for r in result.selected if r.kind == "brief"))
    with open(REPO / "scratch" / "expr-savings.tsv", "w", encoding="utf-8") as fh:
        fh.write("expr\tfreq\tlongform\tcomposed\tsaving\texceptions\n")
        for expr in pool:
            traced = composeOutlineTraced(rulesJoint, expr.tokens, realCtx)
            fh.write(f"{'+'.join(expr.units)}\t{expr.freq:.0f}\t"
                     f"{expr.longformStrokes}\t{len(traced.strokes or ())}\t"
                     f"{traced.saving}\t{traced.exceptions}\n")

    # ---- Phase 3: the expr-rules.tsv report (per-rule attribution over the
    # joint composition) + the composability matrix.
    from collections import defaultdict

    from src.affixbinding import PhonemeKeys, salientPhonemes, simScore
    from util._stenorender import renderFinalStrokesToRTFCRE

    pk = PhonemeKeys(starboard)
    # attaches (keypress) and briefs (beta strokes), in selection order
    rulesFinal = [r for r in result.selected
                  if (r.kind == "attach" and r.keys is not None)
                  or (r.kind == "brief" and r.beta is not None)]
    ruleOf = {(r.units, r.position): r for r in rulesFinal}
    def newStats() -> dict:
        return {"saved": 0.0, "fired": 0.0, "excFreq": 0.0, "exc": [],
                "examples": [], "with": defaultdict(float)}
    stats: dict[tuple, dict] = defaultdict(newStats)
    pairEx: dict[tuple, tuple] = {}
    keyOf = lambda r: (r.units, r.position)
    for expr in pool:
        traced = composeOutlineTraced(rulesJoint, expr.tokens, realCtx)
        if traced.strokes is None:
            continue
        fired = []
        strokesOf = {t.unit: len(t.strokes) for t in expr.tokens}
        for seg in traced.segments:
            if seg.kind == "brief" and seg.rule is not None:
                rule = ruleOf.get((seg.rule.expression, ""))
                if rule is None:
                    continue
                k = keyOf(rule)
                stats[k]["saved"] += expr.freq * (
                    sum(strokesOf.get(u, 1) for u in seg.units) - len(seg.strokes))
                stats[k]["fired"] += expr.freq
                fired.append(k)
                continue
            if seg.kind != "attach" or seg.rule is None:
                continue
            rule = ruleOf.get((seg.rule.expression, seg.rule.position))
            if rule is None:
                continue
            span = len(seg.strokes) or (seg.span[1] - seg.span[0])
            k = keyOf(rule)
            if seg.outcome == "merged":
                stats[k]["saved"] += expr.freq * span
                stats[k]["fired"] += expr.freq
                fired.append(k)
            elif seg.outcome == "standalone":
                stats[k]["saved"] += expr.freq * (span - 1)
                stats[k]["fired"] += expr.freq
                fired.append(k)
            else:
                stats[k]["excFreq"] += expr.freq
                stats[k]["exc"].append((expr.freq, expr.units))
        longformR = renderFinalStrokesToRTFCRE(
            starboard, tuple(s for t in expr.tokens for s in t.strokes))
        composedR = renderFinalStrokesToRTFCRE(starboard, traced.strokes)
        for a in fired:
            for b in fired:
                if a != b:
                    stats[a]["with"][b] += expr.freq
                    pairEx.setdefault(tuple(sorted((a, b))), (0.0, ""))
                    if expr.freq > pairEx[tuple(sorted((a, b)))][0]:
                        pairEx[tuple(sorted((a, b)))] = (
                            expr.freq, f"{' '.join(expr.units)}: {longformR} -> {composedR}")
        for k in fired or []:
            if len(stats[k]["examples"]) < 3:
                stats[k]["examples"].append(
                    f"{' '.join(expr.units)}: {longformR} -> {composedR}")

    phonoOf: dict[str, str] = {}
    for rule in rulesFinal:
        if rule.kind == "brief":
            rule.keySimilarity = 0.0    # a brief's stroke is derived, not a key choice
            continue
        memberPhonos = []
        for unit in rule.units:
            if unit not in phonoOf:
                pairs = resolveTerm(unit, byOrtho)
                phonoOf[unit] = pairs[0][1].phonology if pairs and pairs[0][1] else ""
            memberPhonos.append((phonoOf[unit], rule.freq))
        weights = salientPhonemes(memberPhonos, pk)
        rule.keySimilarity = simScore(frozenset(rule.keys or ()), weights, pk,
                                      rule.position or "prefix")

    with open(REPO / "scratch" / "expr-rules.tsv", "w", encoding="utf-8") as out:
        out.write("rank\tkind\tfamily\texpression\tposition\tkeys\trtfcre\tscore\t"
                  "strokeFreqSaved\tkeySimilarity\texceptionFreq\ttopExceptions\t"
                  "examples\tcomposedWith\n")
        for rank, rule in enumerate(rulesFinal, 1):
            st = stats[keyOf(rule)]
            top = sorted(st["exc"], key=lambda t: -t[0])[:5]
            out.write("\t".join([
                str(rank), rule.kind, rule.family, " ".join(rule.units),
                rule.position,
                ("/".join(",".join(map(str, st)) for st in rule.beta)
                 if rule.kind == "brief"
                 else ",".join(map(str, rule.keys or ()))),
                (renderFinalStrokesToRTFCRE(starboard, tuple(rule.beta))
                 if rule.kind == "brief"
                 else renderFinalStrokesToRTFCRE(
                     starboard, (tuple(sorted(rule.keys or ())),))),
                f"{rule.score:.3e}", f"{st['saved']:.3e}",
                f"{getattr(rule, 'keySimilarity', 0.0):.3f}",
                f"{st['excFreq']:.3e}",
                "; ".join(" ".join(u) for _f, u in top),
                " | ".join(st["examples"]),
                "; ".join(f"{' '.join(bKey[0])}({m:.2e})"
                          for bKey, m in sorted(st["with"].items(),
                                                key=lambda kv: -kv[1])[:4]),
            ]) + "\n")
    with open(REPO / "scratch" / "expr-composability.tsv", "w", encoding="utf-8") as out:
        out.write("ruleA\truleB\tjoint_freq\tworked_example\n")
        seenPairs = set()
        for rule in rulesFinal:
            for bKey, m in stats[keyOf(rule)]["with"].items():
                pair = tuple(sorted([(rule.units, rule.position), bKey]))
                if pair in seenPairs or m < 1e6:
                    continue
                seenPairs.add(pair)
                ex = pairEx.get(pair, (0.0, ""))[1]
                out.write(f"{' '.join(rule.units)}\t{' '.join(bKey[0])}\t{m:.3e}\t{ex}\n")
    print(f"report: scratch/expr-rules.tsv ({len(rulesFinal)} rules), "
          f"expr-composability.tsv ({len(seenPairs)} pairs >= 1e6)")

    # ---- Forced briefs (user decision 2026-10-01): tao entries with no
    # coverage from the selected rules get invented strokes from their OWN
    # budget (FORCED_BRIEF_BUDGET); the same mechanic adds words later.
    from src.expressionrules import FORCED_BRIEF_BUDGET, deriveBriefStroke
    from src.expressions import BriefRule

    taoSet = {tuple(p.split("=")[0] for p in row["phonologies"].split(",") if p)
              for row in rows if "tao" in row["flags"].split(",")}
    # selected briefs already own their expressions and their strokes
    selBriefUnits = {r.units for r in result.selected if r.kind == "brief"}
    covered = set(selBriefUnits)
    for expr in pool:
        if composeOutlineTraced(rulesJoint, expr.tokens, realCtx).saving > 0:
            covered.add(expr.units)
    forced = sorted((e for e in pool if e.units in taoSet
                     and e.units not in covered
                     and e.longformStrokes >= 2),
                    key=lambda e: (-e.freq, e.units))[:FORCED_BRIEF_BUDGET]
    briefs: list[tuple] = []
    takenStrokes: set = {r.beta[0] for r in result.selected
                         if r.kind == "brief" and r.beta is not None}
    takenStrokes |= selBriefTaken
    for expr in forced:
        got = deriveBriefStroke(expr, realCtx, takenStrokes,
                                freeChords=keypresses)
        if got is None:
            continue
        stroke, label = got
        takenStrokes.add(stroke)
        briefs.append((expr, stroke, label))
    briefRules = tuple(BriefRule(e.units, (st,)) for e, st, _l in briefs)
    withBriefs = Rules(attaches=rulesJoint.attaches,
                       briefs=rulesJoint.briefs + briefRules)
    savingBrief = 0.0
    bShadows: list = []
    byOutline: dict = {}
    for expr in pool:
        traced = composeOutlineTraced(withBriefs, expr.tokens, realCtx)
        if traced.strokes is None:
            continue
        savingBrief += expr.freq * traced.saving
        if traced.saving > 0 and traced.strokes in realCtx.finalOutlines:
            bShadows.append((expr.units, traced.strokes))
        byOutline.setdefault(traced.strokes, []).append(expr.units)
    bCollisions = {o: us for o, us in byOutline.items() if len(set(us)) > 1}
    with open(REPO / "scratch" / "expr-briefs.tsv", "w", encoding="utf-8") as out:
        out.write("expr\tfreq\tderivation\tstroke\trtfcre\t"
                  "longform_strokes\tstrokes_saved\n")
        for expr, stroke, label in briefs:
            out.write(f"{' '.join(expr.units)}\t{expr.freq:.0f}\t{label}\t"
                      f"{','.join(map(str, stroke))}\t"
                      f"{renderFinalStrokesToRTFCRE(starboard, (stroke,))}\t"
                      f"{expr.longformStrokes}\t{expr.longformStrokes - 1}\n")
    with open(OUT_TSV, "a", encoding="utf-8") as out:
        for rank, (expr, stroke, label) in enumerate(briefs, len(rulesFinal) + 1):
            out.write("\t".join([str(rank), "brief", "", " ".join(expr.units),
                                  "", ",".join(map(str, stroke)),
                                  renderFinalStrokesToRTFCRE(starboard, (stroke,)),
                                  f"{expr.freq * (expr.longformStrokes - 1):.3e}",
                                  f"{expr.freq * (expr.longformStrokes - 1):.3e}",
                                  label, "0", "", "", ""]) + "\n")
    print(f"briefs: {len(briefs)} created ({len(forced)} uncovered tao entries, "
          f"budget {FORCED_BRIEF_BUDGET}) -> scratch/expr-briefs.tsv")
    print(f"with briefs: saving {savingBrief:.3e}, shadows {len(bShadows)}, "
          f"collisions {len(bCollisions)}")
    for units, outline in bShadows[:3]:
        print("  SHADOW", " ".join(units), outline)
    for outline, exprs in list(bCollisions.items())[:3]:
        print("  COLLISION", outline, [" ".join(u) for u in exprs[:4]])
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
