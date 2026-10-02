import json, time
from src import affixes as A, affixrules as R
from src.affixbinding import PhonemeKeys, enumerateKeypresses
from src.affixdecisions import loadDecisions
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
sb = Starboard.fromJSONFile("starboard3h.json")
ph, dis, _w, _l = loadPhoneticAndDisambiguatedTheory(sb)
rec, _ = A.extractRecords(ph, dis)
d = loadDecisions()
pool = A.buildCandidates(rec, A.loadSeeds()[0], decisions=d)
ctx = A.SimContext(sb, rec); pk = PhonemeKeys(sb); kp = enumerateKeypresses(sb, ctx)
byKey = {(c.position, c.ortho, c.phono): c for c in pool.values() if c.k == 1}
for r in json.load(open("affix_rules.json")):
    if r["rank"] not in (1, 3, 11): continue
    c = byKey[(r["position"], r["ortho"], r["phono"])]
    for n in (5, 15, 30):
        R.MAX_ALTERNATIVES = n
        rule = R.Rule(c.position, c, [c] + A.growScopedForms(c, d), score=0.0)
        t = time.time(); R.chooseRuleKeypress(rule, pk, ctx, kp)
        print(f"rank {r['rank']} MAX_ALTERNATIVES={n}: keys {rule.keys} score {rule.score:.0f} ({time.time()-t:.0f}s)", flush=True)
