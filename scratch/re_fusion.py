import pickle, sys, collections
sys.path.insert(0, ".")
from src import affixes as A, affixrules as R
from src.affixes import Binding, RULE, PREFIX, simulate, poolCarriers
from util import affix_scan as S
A.RULE_PARTIAL_OVERLAP = True
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == "H")
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, kps, lem = S._engine(cands, records, starboard)
def roots(orthos):
    out = []
    for o in orthos:
        rs = [c for k, c in cands.items() if k[0] == PREFIX and k[1] == 1 and k[3] == o]
        out += rs
    return out
def evalKey(forms, keys):
    cs = poolCarriers(forms)
    (res,) = simulate([(Binding(PREFIX, RULE, keys), cs)], ctx, boundaryRisk=False)
    sc, ben, exc, ef, top = R.ruleScoreFromResults(res, 0, len(forms))
    return dict(score=sc, benefit=ben, exc=exc, excFreq=ef, top=top, words=len(cs),
                hits=sum(1 for r in res if r.gain > 0))
def best(forms):
    rule = R.Rule(PREFIX, forms[0], forms)
    R.chooseRuleKeypress(rule, pk, ctx, kps)
    return rule
groups = {"re": roots(["re"]), "ré": roots(["ré"]), "ré+rhé+réh+rai+raie+ra": roots(["ré", "rhé", "réh", "rai", "raie", "ra"]),
          "re+ré (merged)": roots(["re", "ré"]), "re+ré+variants (all of rank 2+17)": roots(["re", "ré", "rhé", "réh", "rai", "raie", "ra"])}
K2, K17 = (16, 19), (3, 4, 16)
print("group | form count | on key (16,19) | on key (3,4,16) | best key found")
for name, forms in groups.items():
    a, b = evalKey(forms, K2), evalKey(forms, K17)
    rule = best(forms)
    print(f"{name}: forms {len(forms)}, words {a['words']}")
    for lab, r in (("(16,19)", a), ("(3,4,16)", b)):
        print(f"    on {lab:9} score {r['score']:7.0f} benefit {r['benefit']:7.0f} hits {r['hits']} hard exc {r['exc']} (freq {r['excFreq']:.0f}) {r['top'][:5]}")
    print(f"    best key {rule.keys}: score {rule.score:.0f} benefit {rule.strokeFreqSaved:.0f} exc {rule.wordExceptions} (freq {rule.exceptionFreq:.0f}) {rule.topExceptions[:6]}")
