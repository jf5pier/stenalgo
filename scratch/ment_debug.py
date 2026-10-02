import pickle, sys
sys.path.insert(0, ".")
from src import affixrules as R
from src.affixes import Binding, RULE, SUFFIX, simulate, poolCarriers
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, kp, lem = S._engine(cands, records, starboard)
root = next(c for k, c in cands.items() if k[0] == SUFFIX and k[1] == 1 and k[3] == "ment")
idx = R.childrenIndex(cands)
rule = R.buildCandidateRule(root, idx)
print("forms:", [(f.k, f.ortho[:40], len(f.carriers)) for f in rule.forms])
pooled = poolCarriers(rule.forms)
print("pooled", len(pooled), "spans", {s: sum(1 for c in pooled if c.span == s) for s in (1,2,3)})
(res,) = simulate([(Binding(SUFFIX, RULE, (20,21,25)), pooled)], ctx, boundaryRisk=False)
sc, b, exc, ef, top = R.ruleScoreFromResults(res, R.exclusionCountOf(rule.forms), len(rule.forms))
print("pooled real rule: score", sc, "benefit", b, "exc", exc, ef, top)
for r in res:
    if r.carrier.rec.ortho in ("seulement", "moment"):
        print(r.carrier.rec.ortho, r.carrier.start, r.carrier.span, r.carrier.rec.base, r.gain, r.reason, r.newBase)
one = [c for c in root.carriers if c.rec.ortho == "seulement"][0]
print("mine:", one.start, one.span, one.rec.base, one.rec.orthoSylls)
