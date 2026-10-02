"""Bench for chooseRuleKeypress speedups (PLAN_2026-09-29-affix-scan-speedup.md).
Usage: choose_bench.py OUT.json   -- dumps keys/score/... per rule + wall times; compare dumps."""
import json, pickle, random, sys, time
from src import affixrules as R
from util import affix_scan as S

out = sys.argv[1]
starboard = S.loadStarboard()
records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
anchors = sorted(R.anchorKeys(cands), key=lambda k: (-len(cands[k].carriers), k))
big = anchors[:6]
random.seed(1)
small = random.sample(anchors[6:], 10)
dump, times = {}, {}
for k in big + small:
    rule = R.buildCandidateRule(cands[k], idx)
    t = time.time()
    R.chooseRuleKeypress(rule, pk, ctx, keypresses)
    times[str(k)] = round(time.time() - t, 2)
    dump[str(k)] = dict(keys=rule.keys, score=rule.score, saved=rule.strokeFreqSaved,
                        exc=rule.wordExceptions, excFreq=rule.exceptionFreq, top=rule.topExceptions,
                        alts=rule.alternatives, sim=rule.keySimilarity,
                        forms=[f.ortho for f in rule.forms])
    print(k[3][:30], times[str(k)], "s", flush=True)
json.dump(dump, open(out, "w"), sort_keys=True, indent=1, default=list)
print("total", round(sum(times.values()), 1), "s")
open("scratch/choose-bench-times.txt", "a").write(f"{out}\ttotal {sum(times.values()):.1f}s\t{times}\n")
