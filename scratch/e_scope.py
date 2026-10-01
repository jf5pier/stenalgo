"""Rank 8 (`é`, keys (2,5)): k=2 scope by the PHONOLOGY of the next syllable."""
import re, sys, collections
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402

rule = loadRule(8); assert rule["root"] == "é"; rule["keys"] = [2, 5]   # keys of the current sweep table (the by-anchor JSON is stale)
sc = Scorer(rule, True, "H")
phon = {}
for c in sc.ones: phon[c.rec.idx] = c.rec.phonoSylls[c.start + c.span]
print(len(sc.ones), "carriers; root", sc.root.ortho, sc.root.phono, "keys", sc.keys, flush=True)
orth = dict(sc.neigh); sc.neigh = dict(phon); sc.syllables = sorted(set(phon.values())); sc.cache = {}
C = "ptkbdgfsSvzZmnNlRjw"; cur = sc.currentScope()
curPhon = {phon[i] for i, o in orth.items() if o in cur}
def pat(rx):
    r = re.compile(rx); return frozenset(s for s in sc.syllables if r.fullmatch(s))
rows = [("anchor alone", frozenset()), ("current list", frozenset(curPhon)), ("C*i", pat(f"[{C}]*i")), ("C{1,2}i", pat(f"[{C}]{{1,2}}i")),
        ("C+i", pat(f"[{C}]+i")), ("C*[iy]", pat(f"[{C}]*[iy]")), ("C*[ie]", pat(f"[{C}]*[ie]")), ("C*V", pat(f"[{C}]*[^{C}]")), ("every neighbour", frozenset(sc.syllables))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc (freq) | objective(5) |\n|---|---|---|---|---|---|---|")
for label, m in rows:
    r = sc.score(m)
    print(f"| {label} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} ({r['excFreq']:.1f}) | {sc.objective(r):.0f} |", flush=True)
zero = sc.score(frozenset()); fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
by = collections.defaultdict(list)
for i, s in phon.items(): by[s].append(i)
print("\nlist phonologies:", sorted(curPhon), "\nbest single followers of `é` (alone vs anchor alone):")
for s in sorted(by, key=lambda s: -sum(fq[i] for i in by[s]))[:26]:
    r = sc.score(frozenset([s]))
    ex = ", ".join(sorted({sc.byIdx[i].rec.ortho for i in by[s]}, key=lambda o: -max(fq[i] for i in by[s] if sc.byIdx[i].rec.ortho == o))[:3])
    print(f"  {s:6} words {len(by[s]):4} freq {sum(fq[i] for i in by[s]):7.1f} d_obj {sc.objective(r)-sc.objective(zero):+6.0f} fb {r['fallbacks']:3} inList {'yes' if s in curPhon else 'NO '} {ex}")
