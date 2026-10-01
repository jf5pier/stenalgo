"""Rank 3 (`en`): is the 2-stroke scope a phonological pattern C*@ (consonants + nasal vowel) on the next syllable?"""
import re, sys
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402

rule = loadRule(3)
sc = Scorer(rule, True, "H")
# re-key the neighbours by PHONOLOGY of the neighbour syllable
sc.neigh = {}
for c in sc.ones:
    j = c.start + c.span
    sc.neigh[c.rec.idx] = c.rec.phonoSylls[j]
sc.syllables = sorted(set(sc.neigh.values()))
C = "ptkbdgfsSvzZmnNlRjw"
cur = sc.currentScope()
curPhon = set()
for c in sc.ones:
    if c.rec.orthoSylls[c.start + c.span] in cur:
        curPhon.add(sc.neigh[c.rec.idx])
def pat(rx):
    r = re.compile(rx)
    return frozenset(s for s in sc.syllables if r.fullmatch(s))
rows = [("anchor alone", frozenset()),
        ("current list (as phonologies)", frozenset(curPhon)),
        (f"C*@", pat(f"[{C}]*@")), (f"C+@", pat(f"[{C}]+@")), (f"C{{1,2}}@", pat(f"[{C}]{{1,2}}@")),
        ("C*[@5§1] (any nasal vowel)", pat(f"[{C}]*[@5§1]")), ("C*@C* (nasal + coda)", pat(f"[{C}]*@[{C}]*")),
        ("every neighbour", frozenset(sc.syllables))]
print(len(sc.ones), "carriers;", len(sc.syllables), "distinct neighbour phonologies; current list =", sorted(curPhon))
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc (freq) | objective(5) |\n|---|---|---|---|---|---|---|")
for label, m in rows:
    r = sc.score(m)
    print(f"| {label} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} ({r['excFreq']:.1f}) | {sc.objective(r):.0f} |", flush=True)
ca = pat(f"[{C}]*@")
print("C*@ phonologies:", sorted(ca))
r = sc.score(ca); print("C*@ fallbacks:", r["fallbackTop"])
# nasal-vowel followers not in the current list, with words/freq
fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
rest = {}
for i, s in sc.neigh.items():
    if s in ca and s not in curPhon:
        rest.setdefault(s, []).append(sc.byIdx[i].rec.ortho)
print("C*@ syllables outside the current list:", {s: len(v) for s, v in sorted(rest.items(), key=lambda x: -len(x[1]))[:15]})
