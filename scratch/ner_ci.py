import sys, re
sys.argv = ["x", "29", "ner", "18,19,20", "né"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
z = sc.objective(sc.score(frozenset()))
sets = [("C{1,2}[i°]", p(f"[{C}]{{1,2}}[i°]")), ("C{1,2}i", p(f"[{C}]{{1,2}}i")), ("C{1,2}°", p(f"[{C}]{{1,2}}°")),
        ("C{1,2}[i°] minus d (dîné) and fouiné-like", p(f"[{C}]{{1,2}}[i°]") - {"di", "fwi"}),
        ("C\\{d}{1,2}[i°]", p(f"[{C.replace('d','')}]{{1,2}}[i°]"))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:4]}", flush=True)
print("C{1,2}[i°] phonologies:", sorted(sets[0][1]))
