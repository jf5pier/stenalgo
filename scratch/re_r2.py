import pickle, sys, collections
sys.path.insert(0, ".")
from src.affixes import PREFIX
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
for ph in ("R2", "R°"):
    c = next(c for k, c in cands.items() if k[0] == PREFIX and k[1] == 1 and k[3] == "re" and k[2] == ph)
    print(ph, len(c.carriers), "words; first syllable phonology of the whole word for a few:")
    for x in sorted(c.carriers, key=lambda x: -x.rec.frequency)[:6]:
        print("   ", x.rec.ortho, x.rec.phonoSylls, x.rec.gramCat)
    if ph == "R2":
        nxt = collections.Counter(x.rec.ortho[2:3] for x in c.carriers)
        print("  letter after 're' (R2 words):", nxt.most_common(12))
        print("  spelled 'reu':", sum(1 for x in c.carriers if x.rec.ortho.startswith("reu")))
        print("  more:", ", ".join(x.rec.ortho for x in sorted(c.carriers, key=lambda x: -x.rec.frequency)[6:40]))
