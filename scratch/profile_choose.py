import pickle, time, cProfile, pstats
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard()
t = time.time(); records = S.loadRecords(starboard, False); print("records", time.time() - t)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
t = time.time(); ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard); print("engine", time.time() - t)
idx = R.childrenIndex(cands)
anchors = R.anchorKeys(cands)
rules = {k: R.buildCandidateRule(cands[k], idx) for k in anchors}
top = sorted(anchors, key=lambda k: -R._upperBound(rules[k]))[:6]
times = []
def run():
    for k in top:
        t = time.time(); R.chooseRuleKeypress(rules[k], pk, ctx, keypresses)
        times.append((round(time.time() - t, 1), k[3][:30], len(rules[k].forms), len(R.poolCarriers(rules[k].forms))))
cProfile.run("run()", "scratch/prof2.out")
print(times)
pstats.Stats("scratch/prof2.out").sort_stats("tottime").print_stats(10)
