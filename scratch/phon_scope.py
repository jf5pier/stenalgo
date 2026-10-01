"""Generic phonology scope scorer for ONE sweep rule (k=1 anchor + a k=2 form), neighbour = syllable absorbed by the 2-stroke form.
Usage: env/bin/python scratch/phon_scope.py RANK ROOT_ORTHO "KEY,KEY,.." [GROWTH_SPELLINGS comma list or -]
RANK = rank in the by-anchor JSON (NOT the sweep table); KEYS = keys of the current sweep table; the neighbour list is taken from the rule."""
import re, sys, collections, pickle
sys.path.insert(0, ".")
rank, rootOrtho, keys = int(sys.argv[1]), sys.argv[2], [int(k) for k in sys.argv[3].split(",")]
growth = None if len(sys.argv) < 5 or sys.argv[4] == "-" else set(sys.argv[4].split(","))
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402
rule = loadRule(rank); assert rule["root"] == rootOrtho, rule["root"]
rule["keys"] = keys
rule["anchors"][0]["anchor"] = rootOrtho
sc = Scorer(rule, True, "H")
phon, first = {}, {}
for c in sc.ones:
    j = c.start - 1 if sc.pos == "suffix" else c.start + c.span
    phon[c.rec.idx] = c.rec.phonoSylls[j]
    first[c.rec.idx] = c.rec.orthoSylls[c.start]
print(len(sc.ones), "carriers; root", sc.root.ortho, repr(sc.root.phono), "keys", sc.keys, flush=True)
orth = dict(sc.neigh)
sc.neigh = {i: (p if (growth is None or first[i] in growth) else "∅") for i, p in phon.items()}
sc.syllables = sorted(set(sc.neigh.values()) - {"∅"}); sc.cache = {}
C = "ptkbdgfsSvzZmnNlRjw"; cur = sc.currentScope()
curPhon = {phon[i] for i, o in orth.items() if o in cur and sc.neigh[i] != "∅"}
def pat(rx):
    r = re.compile(rx); return frozenset(s for s in sc.syllables if r.fullmatch(s))
vowels = sorted({s[-1] for s in curPhon if s and s[-1] not in C} | {s[-2] for s in curPhon if len(s) > 1 and s[-1] in C and s[-2] not in C}) if curPhon else []
rows = [("anchor alone", frozenset()), ("current list", frozenset(curPhon))]
if vowels:
    v = "".join(vowels)
    rows += [(f"C*[{v}] (list vowels)", pat(f"[{C}]*[{v}]")), (f"C{{1,2}}[{v}]", pat(f"[{C}]{{1,2}}[{v}]")), (f"C*[{v}]C*", pat(f"[{C}]*[{v}][{C}]*"))]
rows += [("C*V (any single vowel)", pat(f"[{C}]*[^{C}]")), ("every neighbour", frozenset(sc.syllables))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc (freq) | objective(5) |\n|---|---|---|---|---|---|---|")
for label, m in rows:
    r = sc.score(m)
    print(f"| {label} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} ({r['excFreq']:.1f}) | {sc.objective(r):.0f} |", flush=True)
zero = sc.score(frozenset()); fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
by = collections.defaultdict(list)
for i, s in sc.neigh.items():
    if s != "∅": by[s].append(i)
print("\nlist phonologies:", sorted(curPhon), "\nbest single neighbours (alone vs anchor alone):")
for s in sorted(by, key=lambda s: -sum(fq[i] for i in by[s]))[:24]:
    r = sc.score(frozenset([s]))
    ex = ", ".join(sorted({sc.byIdx[i].rec.ortho for i in by[s]}, key=lambda o: -max(fq[i] for i in by[s] if sc.byIdx[i].rec.ortho == o))[:3])
    print(f"  {s:6} words {len(by[s]):4} freq {sum(fq[i] for i in by[s]):7.1f} d_obj {sc.objective(r)-sc.objective(zero):+6.0f} fb {r['fallbacks']:3} inList {'yes' if s in curPhon else 'NO '} {ex}")
