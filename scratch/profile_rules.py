import pickle, time, cProfile, pstats, random, sys
from src import affixrules as R
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
idx = R.childrenIndex(cands)
anchors = R.anchorKeys(cands)
random.seed(1)
sample = random.sample(anchors, 150)
times = []
def run():
    for k in sample:
        t = time.time(); r = R.buildCandidateRule(cands[k], idx); R._upperBound(r)
        times.append((time.time() - t, k, len(r.forms), len(R.descendantsOf(cands[k], idx))))
cProfile.run("run()", "scratch/prof.out")
print("total", sum(t[0] for t in times), "for 150 of", len(anchors), "anchors")
for t in sorted(times, reverse=True)[:8]: print(t)
pstats.Stats("scratch/prof.out").sort_stats("cumulative").print_stats(12)
