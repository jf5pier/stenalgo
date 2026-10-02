import pickle, sys
sys.path.insert(0, ".")
from src import affixes as A, affixrules as R
from src.affixes import Binding, RULE, PREFIX, simulate, poolCarriers
from util import affix_scan as S
A.RULE_PARTIAL_OVERLAP = True
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == "H")
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, kps, lem = S._engine(cands, records, starboard)
def root(o, ph): return next(c for k, c in cands.items() if k[0] == PREFIX and k[1] == 1 and k[3] == o and k[2] == ph)
RO, R2, RE_ = root("re", "R°"), root("re", "R2"), root("ré", "Re")
def ev(forms, keys, label):
    cs = poolCarriers(forms)
    (res,) = simulate([(Binding(PREFIX, RULE, keys), cs)], ctx, boundaryRisk=False)
    _s, ben, exc, ef, top = R.ruleScoreFromResults(res, 0, len(forms))
    r2 = {c.rec.idx for c in R2.carriers}
    r2res = [r for r in res if r.carrier.rec.idx in r2]
    r2exc = [r.carrier.rec.ortho for r in sorted(r2res, key=lambda r: -r.carrier.rec.frequency) if r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS]
    print(f"{label:28} key {str(keys):10} words {len(cs):5} benefit {ben:6.0f} hard exc {exc:4} (freq {ef:5.0f}) | R2 subset: {sum(1 for r in r2res if r.gain>0)}/{len(r2res)} gain, exc: {r2exc[:8]}")
    return res
for keys in ((16, 19),):
    ev([RO], keys, "R° alone")
    ev([R2], keys, "R2 alone")
    ev([RO, R2], keys, "R° + R2")
    ev([RO, R2, root('ré','Re')], keys, "R° + R2 + ré")
for label, forms in (("R° alone", [RO]), ("R° + R2", [RO, R2]), ("R° + R2 + ré", [RO, R2, root('ré','Re')])):
    rule = R.Rule(PREFIX, forms[0], forms); R.chooseRuleKeypress(rule, pk, ctx, kps)
    print(f"best key for {label}: {rule.keys} benefit {rule.strokeFreqSaved:.0f} exc {rule.wordExceptions} (freq {rule.exceptionFreq:.0f}) alts {[(round(s), k) for s, k in rule.alternatives[:3]]}")

print("---- which R° words newly fail when the R2 words join, on (16,19)?")
def excset(forms):
    cs = poolCarriers(forms)
    (res,) = simulate([(Binding(PREFIX, RULE, (16, 19)), cs)], ctx, boundaryRisk=False)
    return {r.carrier.rec.idx: (r.carrier.rec.ortho, r.reason, r.carrier.rec.frequency) for r in res if r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS}, {r.carrier.rec.idx: r for r in res}
a, _ = excset([RO]); b, resb = excset([RO, R2])
r2ids = {c.rec.idx for c in R2.carriers}
new = {i: v for i, v in b.items() if i not in a and i not in r2ids}
print(len(new), "R° words newly failing:", sorted(((round(v[2], 1), v[0], v[1]) for v in new.values()), reverse=True)[:14])
# what do they collide with?
byBase = {}
for i, r in resb.items():
    if r.newBase is not None: byBase.setdefault(r.newBase, []).append(r.carrier.rec.ortho)
import itertools
shown = 0
for i, v in sorted(new.items(), key=lambda kv: -kv[1][2]):
    r = resb[i]
    partners = [x.carrier.rec.ortho for x in resb.values() if x.newBase is not None and x.newBase == r.newBase and x.carrier.rec.ortho != v[0]]
    print("  ", v[0], v[1], "->", r.newBase, "same outline as R2?:", [p for p in partners][:4])
    shown += 1
    if shown >= 6: break
