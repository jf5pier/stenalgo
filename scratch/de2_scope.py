"""Rank 5 (`de` = d°, keys (16,19)): scope of the 2-stroke form by next syllable (spelling and phonology)."""
import re, sys, collections
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402

rule = loadRule(5)
sc = Scorer(rule, True, "H")
root = [c for c in __import__("pickle").load(open("scratch/affix-pool.pickle", "rb")).values()
        if c.position == "prefix" and c.k == 1 and c.ortho == "de" and c.phono == "d°"][0]
sc.root = root; sc.ones = []; sc.neigh = {}; phon = {}
for c in root.carriers:
    if len(c.rec.orthoSylls) != len(c.rec.base): continue
    j = c.start + c.span
    if j < len(c.rec.orthoSylls):
        sc.ones.append(c); sc.neigh[c.rec.idx] = c.rec.orthoSylls[j]; phon[c.rec.idx] = c.rec.phonoSylls[j]
sc.byIdx = {c.rec.idx: c for c in sc.ones}; sc.syllables = sorted(set(sc.neigh.values())); sc.cache = {}
cur = sc.currentScope() & set(sc.syllables)
print(len(sc.ones), "carriers,", len(sc.syllables), "distinct next syllables; keys", sc.keys, "; current list", sorted(cur), flush=True)
zero = sc.score(frozenset())
fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
def row(label, m):
    r = sc.score(frozenset(m))
    print(f"| {label} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} ({r['excFreq']:.1f}) | {sc.objective(r):.0f} |", flush=True)
print("| scope | syllables | 2-stroke words | fallbacks (freq) | benefit | hard exc (freq) | objective(5) |\n|---|---|---|---|---|---|---|")
row("anchor alone", []); row("current list", cur)
row("every next syllable", sc.syllables)
by = collections.defaultdict(list)
for i, s in sc.neigh.items(): by[s].append(i)
order = sorted(by, key=lambda s: -sum(fq[i] for i in by[s]))
print("\nnext syllables after `de`, alone vs anchor alone (d_obj = objective(5) change):")
gain = {}
for s in order[:40]:
    r = sc.score(frozenset([s])); gain[s] = sc.objective(r) - sc.objective(zero)
    ph = collections.Counter(phon[i] for i in by[s]).most_common(1)[0][0]
    ex = ", ".join(sorted({sc.byIdx[i].rec.ortho for i in by[s]}, key=lambda o: -max(fq[i] for i in by[s] if sc.byIdx[i].rec.ortho == o))[:3])
    print(f"  {s:6} /{ph}/ words {len(by[s]):3} freq {sum(fq[i] for i in by[s]):7.1f} d_obj {gain[s]:+6.0f} fb {r['fallbacks']:2} inList {'yes' if s in cur else 'NO '} {ex}")
pos = [s for s in by if s not in gain]

print("\n| candidate scope | syllables | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) |\n|---|---|---|---|---|---|---|")
syl = set(sc.syllables)
cands = {
  "current list (10)": cur,
  "list minus ba, re": cur - {"ba", "re"},
  "man, ve, vi": {"man", "ve", "vi"},
  "man, ve": {"man", "ve"},
  "[mv](an|e|i) as regex": {s for s in syl if re.fullmatch("[mv](an|e|i)", s)},
  "[mv](an|e|i|ien|ri|oi|eu)": {s for s in syl if re.fullmatch("[mv](an|e|i|ien|ri|oi|eu)", s)},
  "[mv]+ any vowel-ish (m|v)\\w{1,3}": {s for s in syl if re.fullmatch("[mv]\\w{1,3}", s)},
  "v(e|i|ien|ri) + man": {s for s in syl if re.fullmatch("v(e|i|ien|ri)|man", s)},
}
for k, m in cands.items():
    r = sc.score(frozenset(m))
    print(f"| {k} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {sc.objective(r):.0f} |", flush=True)
r = sc.score(frozenset({s for s in syl if re.fullmatch("[mv]\\w{1,3}", s)}))
print("fallbacks of the wide [mv] scope:", r["fallbackTop"])
