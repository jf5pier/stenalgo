import pickle
from collections import defaultdict
from src import affixes as A
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
anchors = [c for c in cands.values() if c.isAnchor and c.k == 1 and not c.mergeParts and not c.isGeneralized]
g = defaultdict(list)
for c in anchors:
    onset, rest = A._onsetRest(c.phono)
    g[(c.position, c.ortho, rest)].append((onset, c))
rows = []
for (pos, ortho, rest), m in g.items():
    if len(m) < 2:
        continue
    m.sort(key=lambda x: -x[1].freq)
    for onset, c in m[1:]:
        rows.append((pos, ortho, rest, m[0][0], m[0][1].freq, onset, c.freq, len(c.carriers)))
print(len(rows), "same-spelling, different-onset pairs; total freq of the smaller side", round(sum(r[6] for r in rows)))
for r in sorted(rows, key=lambda r: -r[6])[:25]:
    print(f"  {r[0]:6} {r[1][:12]:12} rest={r[2]:5} main onset {r[3]!r:5} f={r[4]:8.0f} | onset {r[5]!r:5} f={r[6]:7.1f} carriers={r[7]}")
