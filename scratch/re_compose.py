import re, sys
sys.path.insert(0, ".")
from scratch.affix_scope_table import Scorer, loadRule
sc = Scorer(loadRule(2), True, "H")
C = "[^aeiouyàâäéèêëîïôöùûüœ]"
base = frozenset(s for s in sc.syllables if re.fullmatch(C + "+ar", s))
z = sc.score(frozenset()); r0 = sc.score(base)
print("anchor alone", round(sc.objective(z)), "| C+ar", round(sc.objective(r0)), r0["fallbacks"], "fallbacks")
# greedy: add the literal syllable with best marginal objective, rescoring the union
chosen, cur = [], base
cands = [s for s in sc.syllables if s not in base]
# prefilter on single-syllable marginal to keep it fast
single = sorted(cands, key=lambda s: -(sc.objective(sc.score(frozenset([s]))) - sc.objective(z)))[:60]
for step in range(10):
    best = max(single, key=lambda s: sc.objective(sc.score(cur | {s})) if s not in cur else -1e9)
    cur = cur | {best}; chosen.append(best); r = sc.score(cur)
    print(f"+{best:8s} atoms {2+len(chosen)}  objective {sc.objective(r):.0f}  benefit {r['benefit']:.0f}  words {r['twoWords']}  fallbacks {r['fallbacks']} (freq {r['fallbackFreq']:.0f})")
