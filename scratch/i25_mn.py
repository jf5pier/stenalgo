import sys, re, collections
sys.argv = ["x", "25", "e|hi|hy|i|y|î", "16,17,19", "i"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
V = f"[^{C}]"
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
z = sc.objective(sc.score(frozenset()))
sets = [("[mn]V (m/n + one vowel)", p(f"[mn]{V}")), ("[mnN]V (+ gn)", p(f"[mnN]{V}")), ("[mn][aeiouy] (plain vowels)", p("[mn][aeiouy]")),
        ("[mn][aeiouy°] (+ schwa)", p("[mn][aeiouy°]")), ("[mn]V{1,2}", p(f"[mn]{V}{{1,2}}")), ("[mn]V C* (any coda)", p(f"[mn]{V}[{C}]*")),
        ("[mn][^C]  minus no (innocent)", p(f"[mn]{V}") - {"no"}),
        ("greedy 4: ma ny d@ no", {"ma", "ny", "d@", "no"}), ("[mn]V + d@", p(f"[mn]{V}") | {"d@"}), ("[mn]V + d@ + ta", p(f"[mn]{V}") | {"d@", "ta"})]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:3]}", flush=True)
print("[mn]V phonologies:", sorted(p(f"[mn]{V}")))
