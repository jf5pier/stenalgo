"""Key-search miss check: for each selected rule with more carriers than the sample, evaluate the stage-1 top 60 keys on ALL carriers."""
import json, sys
from src import affixes as A, affixrules as R
from src.affixbinding import PhonemeKeys, enumerateKeypresses, SAMPLE_CARRIERS, salientPhonemes, simScore
from src.affixdecisions import loadDecisions
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
sb = Starboard.fromJSONFile("starboard3h.json")
ph, dis, _w, _l = loadPhoneticAndDisambiguatedTheory(sb)
rec, _ = A.extractRecords(ph, dis)
d = loadDecisions()
pool = A.buildCandidates(rec, A.loadSeeds()[0], decisions=d)
ctx = A.SimContext(sb, rec)
pk = PhonemeKeys(sb); kp = enumerateKeypresses(sb, ctx)
byKey = {(c.position, c.ortho, c.phono): c for c in pool.values() if c.k == 1}
idx = R.childrenIndex(pool)
def full(rule, k, carriers):
    cs, nfb = R.resolveFallbacks(rule, k, carriers, ctx)
    (res,) = A.simulate([(A.Binding(rule.position, A.RULE, k), cs)], ctx)
    sc = R.ruleScoreFromResults(res, R.exclusionCountOf(rule.forms) + nfb, len(rule.forms))[0]
    return sc if R._exceptionRate(res) <= R.MAX_EXCEPTION_RATE else None
for r in json.load(open("affix_rules.json")):
    c = byKey[(r["position"], r["ortho"], r["phono"])]
    rule = R.Rule(c.position, c, [c] + A.growScopedForms(c, d), score=0.0)
    carriers = A.poolCarriers(rule.forms)
    if len(carriers) <= SAMPLE_CARRIERS:
        print(f"{r['rank']:2} {r['ortho']:22} {len(carriers):6} carriers: no sampling", flush=True); continue
    sample = carriers[:SAMPLE_CARRIERS]; groups = R._neighbourGroups(rule.position, sample)
    ex = R.exclusionCountOf(rule.forms)
    st = []
    for k in kp:
        if R._exceptionRateFloor(groups, k, ctx) > R.MAX_EXCEPTION_RATE: continue
        sk, nfb = R.resolveFallbacks(rule, k, sample, ctx)
        (res,) = A.simulate([(A.Binding(rule.position, A.RULE, k), sk)], ctx, boundaryRisk=False)
        sc = R.ruleScoreFromResults(res, ex + nfb, len(rule.forms))[0]
        if sc > 0 and R._exceptionRate(res) <= R.MAX_EXCEPTION_RATE: st.append((sc, k))
    st.sort(key=lambda t: (-t[0], t[1]))
    chosen = tuple(r["keys"]); base = full(rule, chosen, carriers)
    best = (base, chosen, 0)
    for rank, (_s, k) in enumerate(st[:60]):
        if k == chosen: continue
        v = full(rule, k, carriers)
        if v is not None and (best[0] is None or v > best[0]): best = (v, k, rank)
    print(f"{r['rank']:2} {r['ortho']:22} {len(carriers):6} carriers: chosen {chosen} {base and round(base)}; best of top60 {best[1]} {best[0] and round(best[0])} (sample rank {best[2]})", flush=True)
