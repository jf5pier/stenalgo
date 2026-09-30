"""How much is at stake in cluster-onset fusion? (RESUME_2026-09-29 'Idea, not started')"""
import pickle
from collections import defaultdict
from src import affixes as A
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
anchors = [c for c in cands.values() if c.isAnchor and c.k == 1 and not c.mergeParts and not c.isGeneralized]
print(len(anchors), "plain k=1 anchors")
groups = defaultdict(list)
for c in anchors:
    onset, rest = A._onsetRest(c.phono)
    groups[(c.position, rest)].append((onset, c))
multi = {k: v for k, v in groups.items() if len({o for o, _ in v}) > 1}
print(len(groups), "(position, nucleus+coda) groups;", len(multi), "with >1 onset")
rows = []
for (pos, rest), members in multi.items():
    members.sort(key=lambda m: -m[1].freq)
    mainOnset, main = members[0]
    for onset, c in members[1:]:
        if onset == mainOnset:
            continue
        if onset and mainOnset and (onset.endswith(mainOnset) or mainOnset.endswith(onset)):
            kind = "additive"
        else:
            kind = "changed"
        rows.append((kind, pos, rest, mainOnset, main.ortho, main.freq, onset, c.ortho, c.freq, len(c.carriers)))
for kind in ("additive",):
    sel = [r for r in rows if r[0] == kind]
    for pos in ("suffix", "prefix"):
      sel2 = [r for r in sel if r[1] == pos]
      print(f"\n-- {pos}: {len(sel2)} pairs, freq of smaller side {sum(r[8] for r in sel2):.0f}")
      for r in sorted(sel2, key=lambda r: -r[8])[:25]:
        print(f"  rest={r[2]:6} main {r[3]!r:5} {r[4][:14]:14} f={r[5]:8.0f} | {r[6]!r:5} {r[7][:22]:22} f={r[8]:7.1f} carriers={r[9]}")
    continue
    print(f"\n== {kind}: {len(sel)} pairs (vs the group's largest), total freq of the smaller side "
          f"{sum(r[8] for r in sel):.0f}")
    for r in sorted(sel, key=lambda r: -r[8])[:15]:
        print(f"  {r[1]:6} rest={r[2]:6} main {r[3]!r:5} {r[4][:14]:14} f={r[5]:8.0f} | {r[6]!r:5} {r[7][:14]:14} f={r[8]:7.1f} carriers={r[9]}")
