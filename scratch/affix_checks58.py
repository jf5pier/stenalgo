import csv, pickle
import src.affixrules as R
import src.affixes as A
pool = pickle.load(open("scratch/affix-pool.pickle","rb"))
idx = R.childrenIndex(pool)
key = next(k for k,c in pool.items() if c.isAnchor and c.ortho=="man|mand|mant|ment|ments|mmant|mment")
rule = R.buildCandidateRule(pool[key], idx)
cs = {c.rec.ortho: c for c in A.poolCarriers(rule.forms)}
for w in ("heureusement","tellement","seulement"):
    c = cs.get(w); print(w, "carrier" if c else "NOT a carrier", c and (c.span, c.stem))
print("orthos containing '°ment' in pool:", sum("°ment" in c.ortho and c.grownFromKey is None for c in pool.values()))
print("anchors whose ortho ends with ment (suffix):", [c.ortho for c in pool.values() if c.isAnchor and c.position=="suffix" and "ment" in c.ortho])
def load(p): return [(r["position"], r["root"]) for r in csv.DictReader(open(p), delimiter="\t")]
old = load("scratch/baseline-20260927/affix-rules.tsv"); new = load("scratch/affix-sweep/L/affix-rules.tsv")
print("left:", [o for o in old if o not in new]); print("arrived:", [n for n in new if n not in old])
