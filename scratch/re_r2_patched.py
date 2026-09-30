import pickle, sys, collections
sys.path.insert(0, ".")
from src import affixes as A, affixrules as R
from src.affixes import Binding, RULE, PREFIX, simulate, poolCarriers
from util import affix_scan as S
A.RULE_PARTIAL_OVERLAP = True
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == "H")
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ro = collections.Counter(r.base[0] for r in records if r.phonoSylls and r.phonoSylls[0] == "R°" and r.ortho.startswith("re"))
r2c = collections.Counter(r.base[0] for r in records if r.phonoSylls and r.phonoSylls[0] == "R2" and r.ortho.startswith("re"))
print("first strokes seen, R°:", ro.most_common(4), " R2:", r2c.most_common(3))
ROSTROKE = (8, 11, 12)   # the R° stroke shared by all 5,934 R° words
R2STROKE = (8, 11, 13, 14)
print("using R° stroke", ROSTROKE)
def patch(rec):
    if rec.phonoSylls and rec.phonoSylls[0] == "R2" and rec.ortho.startswith("re") and not rec.ortho.startswith("reu") and tuple(rec.base[0]) == R2STROKE:
        object.__setattr__(rec, "base", (ROSTROKE,) + tuple(rec.base[1:]))
        object.__setattr__(rec, "phonoSylls", ("R°",) + tuple(rec.phonoSylls[1:]))
        return 1
    return 0
n = sum(patch(r) for r in records)
n2 = sum(patch(c.rec) for k, cc in cands.items() for c in cc.carriers if k[0] == PREFIX and k[1] == 1 and k[3] == "re" and k[2] == "R2")
print("patched", n, "records in ctx,", n2, "carrier records")
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
    print(f"{label:16} key {str(keys):9} words {len(cs):5} benefit {ben:6.0f} hard exc {exc:4} (freq {ef:4.0f}) | R2 subset {sum(1 for r in r2res if r.gain>0)}/{len(r2res)} gain; exc {r2exc[:6]} ; top exc {top[:6]}")
for keys in ((16, 19),):
    ev([RO], keys, "R° alone"); ev([RO, R2], keys, "R° + R2 (as R°)"); ev([RO, R2, RE_], keys, "R°+R2+ré")
for label, forms in (("R° + R2 (as R°)", [RO, R2]), ("R°+R2+ré", [RO, R2, RE_])):
    rule = R.Rule(PREFIX, forms[0], forms); R.chooseRuleKeypress(rule, pk, ctx, kps)
    print(f"best key for {label}: {rule.keys} benefit {rule.strokeFreqSaved:.0f} exc {rule.wordExceptions} (freq {rule.exceptionFreq:.0f})")
