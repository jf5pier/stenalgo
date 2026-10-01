import pickle, sys, re, collections
sys.path.insert(0, ".")
from src import affixes as A
from src.affixes import Binding, RULE, PREFIX, simulate, isAttested, norm
from util import affix_scan as S
A.RULE_PARTIAL_OVERLAP = True
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, kp, lem = S._engine(cands, records, starboard)
root = max((c for k, c in cands.items() if k[0] == PREFIX and k[1] == 1 and k[3] == "re"), key=lambda c: len(c.carriers))
(res,) = simulate([(Binding(PREFIX, RULE, (16, 19)), root.carriers)], ctx, boundaryRisk=False)
tab = collections.defaultdict(lambda: [0, 0.0, []])
for r in res:
    att = isAttested(PREFIX, r.carrier, lem)
    kind = "hit" if r.gain > 0 else (r.reason or "other")
    t = tab[(att, kind)]; t[0] += 1; t[1] += r.carrier.rec.frequency; t[2].append((r.carrier.rec.frequency, r.carrier.rec.ortho))
print("re carriers: stem-is-a-lemma x outcome (words, freq)")
for (att, kind), (n, f, ex) in sorted(tab.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
    print(f"  stem lemma={att!s:5} {kind:16} {n:5} {f:9.1f}  ", ", ".join(o for _f, o in sorted(ex, reverse=True)[:8]))
# variants ré- / r- straight from the lexicon (lemmas of all records)
lemmas = {r.lemme for r in records}; freq = collections.defaultdict(float)
for r in records: freq[r.lemme] += r.frequency
V = "aeiouyàâäéèêëîïôöùûü"
fam = {"re+": ("re", lambda x: x), "ré+vowel": ("ré", lambda x: x), "r+vowel": ("r", lambda x: x)}
for name, pre in (("ré-", "ré"), ("r-", "r"), ("re-", "re")):
    hits = []
    for l in lemmas:
        if l.startswith(pre) and len(l) > len(pre) + 2:
            stem = l[len(pre):]
            if name != "re-" and stem[0] not in V: continue
            if name == "r-" and l.startswith(("ré", "re")): continue
            if stem in lemmas: hits.append((freq[l], l, stem))
    hits.sort(reverse=True)
    print(f"{name}: {len(hits)} lemmas whose rest is a lemma, freq {sum(h[0] for h in hits):.0f}; top:", ", ".join(f"{l}<{s}" for _f, l, s in hits[:14]))
