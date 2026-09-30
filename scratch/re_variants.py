import pickle, sys
sys.path.insert(0, ".")
from src.affixes import PREFIX
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
for k, c in sorted(cands.items(), key=lambda kv: -len(kv[1].carriers)):
    if k[0] == PREFIX and k[1] == 1 and k[3] in ("re", "ré", "rhé", "réh", "rai", "raie", "ra"):
        ex = sorted(c.carriers, key=lambda x: -x.rec.frequency)
        print(f"ortho {k[3]:5} phono {k[2]:6} words {len(c.carriers):5} :", ", ".join(f"{x.rec.ortho}" for x in ex[:9]))
