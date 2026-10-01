"""Run against the OLD (HEAD checkpoint) code: dump every A7 node of the 2026-09-27-style pool.
Usage (from an old-code worktree root): PYTHONPATH=. python /path/probe_dump_a7.py OUT.pickle"""
import pickle
import sys

import src.affixes as A

records = pickle.load(open("scratch/affix-records.pickle", "rb"))
seedPairs, _ = A.loadSeeds()
pool = A.buildCandidates(records, seedPairs)
out = {}
for key, c in pool.items():
    if c.isGeneralized and not c.slots and c.grownFromKey is None and c.k >= 1:
        out[key] = (c.freq, frozenset(x.rec.idx for x in c.carriers))
pickle.dump(out, open(sys.argv[1], "wb"))
print(len(pool), "pool nodes;", len(out), "A7 nodes")
