import sys, re, collections
sys.argv = ["x", "27", "o", "16,18,19"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
Ci = {s for s in S if re.fullmatch(f"[{C}]{{1,2}}i", s)}
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
V = f"[^{C}]"
z = sc.objective(sc.score(frozenset()))
by = collections.defaultdict(list)
for i, s in sc.neigh.items():
    if s != "∅" and re.fullmatch(f"k{V}", s): by[s].append(sc.byIdx[i].rec.ortho)
print("k+vowel neighbours:", {s: (len(v), sorted(set(v))[:3]) for s, v in by.items()})
sets = [("C{1,2}i", Ci), ("C{1,2}i + k[aeiouy]", Ci | p("k[aeiouy]")), ("C{1,2}i + k[aeiouy°]", Ci | p("k[aeiouy°]")),
        ("C{1,2}i + kV (any vowel)", Ci | p(f"k{V}")), ("C{1,2}i + k[yu]", Ci | p("k[yu]")), ("C{1,2}i + ky", Ci | {"ky"})]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:3]}", flush=True)
