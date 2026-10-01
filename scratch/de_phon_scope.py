"""Rank 4 (`de|des|dé|déh`, keys (11,16,18)): growth only on `dé`-spelled carriers; scope by the neighbour's PHONOLOGY."""
import re, sys, collections
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402
import src.affixrules as RR  # noqa: E402

rule = loadRule(4)
rule["anchors"][0]["anchor"] = "de|des|dé|déh"     # the merged anchor node, not its first part
sc = Scorer(rule, True, "H")
print(len(sc.ones), "carriers with a next syllable; anchor", sc.anchorOrtho, flush=True)
orthoNext = dict(sc.neigh)
sc.neigh = {}
for c in sc.ones:
    sc.neigh[c.rec.idx] = c.rec.phonoSylls[c.start + c.span] if c.rec.orthoSylls[c.start] == "dé" else "∅"
sc.syllables = sorted(set(sc.neigh.values()) - {"∅"})
C = "ptkbdgfsSvzZmnNlRjw"
cur = sc.currentScope()
curPhon = {sc.neigh[c.rec.idx] for c in sc.ones if sc.neigh[c.rec.idx] != "∅" and orthoNext[c.rec.idx] in cur}
print("current list as phonologies:", sorted(curPhon))
def pat(rx):
    r = re.compile(rx); return frozenset(s for s in sc.syllables if r.fullmatch(s))
rows = [("anchor alone", frozenset()), ("current list", frozenset(curPhon)),
        ("C*i", pat(f"[{C}]*i")), ("C{1,2}i", pat(f"[{C}]{{1,2}}i")), ("C+i", pat(f"[{C}]+i")),
        ("C*[iy]", pat(f"[{C}]*[iy]")), ("C*[iyeE2]", pat(f"[{C}]*[iyeE2]")), ("C*V (any single vowel)", pat(f"[{C}]*[^{C}]")),
        ("every dé neighbour", frozenset(sc.syllables))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc (freq) | objective(5) |\n|---|---|---|---|---|---|---|")
for label, m in rows:
    r = sc.score(m)
    print(f"| {label} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} ({r['excFreq']:.1f}) | {sc.objective(r):.0f} |", flush=True)
zero = sc.score(frozenset())
fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
by = collections.defaultdict(list)
for i, s in sc.neigh.items():
    if s != "∅": by[s].append(i)
order = sorted(by, key=lambda s: -sum(fq[i] for i in by[s]))[:30]
print("\ntop neighbour phonologies after `dé`, alone vs anchor alone:")
for s in order:
    r = sc.score(frozenset([s]))
    ex = ", ".join(sorted({sc.byIdx[i].rec.ortho for i in by[s]}, key=lambda o: -max(fq[i] for i in by[s] if sc.byIdx[i].rec.ortho == o))[:3])
    print(f"  {s:6} words {len(by[s]):4} freq {sum(fq[i] for i in by[s]):7.1f} d_obj {sc.objective(r)-sc.objective(zero):+6.0f} fallbacks {r['fallbacks']:3} inList {'yes' if s in curPhon else 'NO '} {ex}")
