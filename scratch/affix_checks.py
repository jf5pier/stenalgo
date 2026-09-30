"""Plan 2026-09-28 §5 acceptance checks 1-4 on scratch/affix-pool.pickle."""
import pickle
import re
import sys

import src.affixes as A

pool = pickle.load(open("scratch/affix-pool.pickle", "rb"))
old = pickle.load(open("scratch/old-a7-nodes.pickle", "rb"))
carrierSets = {k: {(c.rec.idx) for c in v.carriers} for k, v in pool.items()}
freqOf = {}
for v in pool.values():
    for c in v.carriers:
        freqOf[c.rec.idx] = c.rec.frequency
print("pool", len(pool), "anchors", sum(c.isAnchor for c in pool.values()))

print("\n== 1. old A7 coverage (freq>=30)")
byPos = {}
for k, ids in carrierSets.items():
    byPos.setdefault(k[0], []).append((k, ids))
misses = 0; total = 0
oldNodes = [(k, f, ids) for k, (f, ids) in old.items() if f >= 30]
# need old-node freq per carrier -> use freqOf where possible
for k, f, ids in sorted(oldNodes, key=lambda t: -t[1]):
    total += 1
    tot = sum(freqOf.get(i, 0) for i in ids) or 1
    best = (0, None)
    for k2, ids2 in byPos.get(k[0], []):
        inter = ids & ids2
        if not inter:
            continue
        cov = sum(freqOf.get(i, 0) for i in inter) / tot
        if cov > best[0]:
            best = (cov, k2)
    if best[0] < 0.9:
        misses += 1
        print(f"  MISS {k[0]} {k[3]!r} (k={k[1]}, f={f:.0f}, {len(ids)} words): best {best[0]:.2f} by {best[1][3] if best[1] else None!r}")
print(f"  {total} old nodes with freq>=30, {misses} covered < 0.9")

print("\n== 2. seeds with k>=2 reachable")
seedPairs, _ = A.loadSeeds()
orthos = {}
for k in pool:
    orthos.setdefault(k[0], set()).add(k[3])
def flat(o):
    return o.replace("·", "")
for pos, aff in sorted(seedPairs):
    if pos == "suffix" and len(aff) < 2: continue
    # k>=2 seeds: those spanning >=2 syllables in some word; approximate: not an anchor key
    anchorOrthos = {c.ortho for c in pool.values() if c.isAnchor}
    if aff in anchorOrthos or any(aff in (c.variants or []) for c in pool.values() if c.isAnchor):
        continue
    found = any(o.endswith(aff) if pos == "suffix" else o.startswith(aff) or re.match(r".*", o) and False for o in orthos[pos])
    if not found:
        found = any(aff in o.replace("·","") for o in orthos[pos]) 
    if not found:
        print("  no node for", pos, aff)

print("\n== 3. -ité chain")
for l in open("scratch/affix-lattice-trace.txt", encoding="utf-8").read().splitlines()[:8]:
    print("  ", l)

print("\n== 4. renames", A.LATTICE_STATS)
