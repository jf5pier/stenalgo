import sys, re
sys.argv = ["x", "17", "ra|rai|raie|re|rhé|ré|réh", "3,4,16", "ré"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def pat(rx): return {s for s in S if re.fullmatch(rx, s)}
C12 = pat(f"[{C}]{{1,2}}y"); C02 = pat(f"[{C}]{{0,2}}y"); C03 = pat(f"[{C}]{{0,3}}y")
rest = {"a", "fle", "vE"}
sets = [("C{1,2}y alone", C12), ("C{0,2}y alone", C02), ("C{0,3}y alone", C03), ("y alone (bare)", {"y"}),
        ("a + fle + vE + C{1,2}y", rest | C12), ("a + fle + vE + C{0,2}y", rest | C02), ("a + fle + vE + C{0,3}y", rest | C03)]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {sc.objective(r):.0f} | {r['fallbackTop'][:4]}", flush=True)
print("C{0,2}y phonologies:", sorted(C02))
