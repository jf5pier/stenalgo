import sys, re, collections
sys.argv = ["x", "25", "e|hi|hy|i|y|î", "16,17,19", "i"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
by = collections.defaultdict(float)
for i, s in sc.neigh.items():
    if s != "∅": by[s] += fq[i]
cands = {s: {s} for s in sorted(by, key=lambda s: -by[s])[:60]}

cur = set(); best = sc.objective(sc.score(frozenset()))
print("start (anchor alone):", round(best), flush=True)
for step in range(1, 13):
    gains = []
    for name, m in cands.items():
        if m <= cur: continue
        o = sc.objective(sc.score(frozenset(cur | m)))
        gains.append((o, name))
    o, name = max(gains)
    if o <= best + 5: print("stop: no unit adds more than 5"); break
    cur |= cands[name]; best = o
    r = sc.score(frozenset(cur))
    print(f"{step}. + {name:10} -> objective {o:.0f} | 2-stroke {r['twoWords']} fallbacks {r['fallbacks']} ({r['fallbackFreq']:.0f}) benefit {r['benefit']:.0f}", flush=True)
