import json
from src import affixes as A, affixproposals as P, affixrules as R
from src.affixbinding import PhonemeKeys, enumerateKeypresses
from src.affixdecisions import loadDecisions
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
d = loadDecisions()   # committed: has the approved fusion entries
sb = Starboard.fromJSONFile("starboard3h.json")
ph, dis, _w, _l = loadPhoneticAndDisambiguatedTheory(sb)
rec, _ = A.extractRecords(ph, dis)
pool = A.buildCandidates(rec, A.loadSeeds()[0], decisions=d)
ctx = A.SimContext(sb, rec); pk = PhonemeKeys(sb); kp = enumerateKeypresses(sb, ctx)
for key, alone in ((("suffix","ccion|cion|cyon|sion|ssion|tion|tions","sj§"),("suffix","tion","sj§")), (("suffix","ner|nez|nner|nnée|née|nées","ne"),("suffix","ner","ne"))):
    m = next(c for c in pool.values() if c.k == 1 and (c.position, c.ortho, c.phono) == key)
    a = next(c for c in pool.values() if c.k == 1 and (c.position, c.ortho, c.phono) == alone)
    idx = R.childrenIndex(pool)
    fused = P.numbersBest(R.buildCandidateRule(m, idx), pk, ctx, kp)   # committed approved growth (tion|tions, né)
    base = P.numbersBest(R.buildCandidateRule(a, idx), pk, ctx, kp)
    print(key[1][:25], "fused(approved forms)", round(fused.score), "alone", round(base.score), "net", round(fused.score - base.score), flush=True)
