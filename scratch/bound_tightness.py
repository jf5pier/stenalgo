"""Step 2 of PLAN_2026-09-29-affix-scan-speedup.md: is the pass-1 upper bound tight enough to skip keys?"""
import pickle, time
from src import affixrules as R
from src.affixes import Binding, RULE, _newBase, poolCarriers
from src.affixrules import simulate, ruleScoreFromResults, _exceptionRate, exclusionCountOf, MAX_EXCEPTION_RATE
from util import affix_scan as S

starboard = S.loadStarboard()
records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
anchors = sorted(R.anchorKeys(cands), key=lambda k: (-len(cands[k].carriers), k))[:6]
lines = ["# Bound tightness (step 2)", "", "| rule | keys | pass filter | threshold (Nth best) | rate1>5% | ub<=0 | skippable total | bound violations |", "|---|---|---|---|---|---|---|---|"]
for key in anchors:
    rule = R.buildCandidateRule(cands[key], idx)
    carriers = poolCarriers(rule.forms)
    sample = carriers[:R.SAMPLE_CARRIERS]
    excl = exclusionCountOf(rule.forms)
    const = R.EXCLUSION_COST * excl + R.FORM_COST * (len(rule.forms) - 1)
    rows = []
    for k in keypresses:
        b = Binding(rule.position, RULE, k)
        ub = 0.0
        valid = e1 = 0
        for c in sample:
            nb, why, merged = _newBase(b, c, ctx)
            if nb is not None:
                valid += 1
                ub += c.rec.frequency * max(0, c.span if merged else c.span - 1)
            elif why in R.WORD_EXCEPTION_REASONS:
                e1 += 1
        ub -= const
        rate1 = e1 / (valid + e1) if valid + e1 else 0.0
        (res,) = simulate([(b, sample)], ctx, boundaryRisk=False)
        sc = ruleScoreFromResults(res, excl, len(rule.forms))[0]
        ok = sc > 0 and _exceptionRate(res) <= MAX_EXCEPTION_RATE
        rows.append((ub, sc, ok, rate1))
    passing = sorted((sc for ub, sc, ok, rate1 in rows if ok), reverse=True)
    thr = passing[R.MAX_ALTERNATIVES - 1] if len(passing) >= R.MAX_ALTERNATIVES else float("-inf")
    byRate = sum(1 for ub, sc, ok, rate1 in rows if rate1 > MAX_EXCEPTION_RATE)
    byUb0 = sum(1 for ub, sc, ok, rate1 in rows if ub <= 0)
    skippable = sum(1 for ub, sc, ok, rate1 in rows if ub < thr or ub <= 0 or rate1 > MAX_EXCEPTION_RATE)
    rateViol = sum(1 for ub, sc, ok, rate1 in rows if rate1 > MAX_EXCEPTION_RATE and ok)
    viol = sum(1 for ub, sc, ok, rate1 in rows if ub + 1e-6 < sc)
    lines.append(f"| {key[3][:25]} | {len(rows)} | {len(passing)} | {thr:.0f} | {byRate} | {byUb0} | {skippable} | {viol + rateViol} |")
    print(lines[-1], flush=True)
open("scratch/bound-tightness.md", "w").write("\n".join(lines) + "\n")
