import sys, re
sys.argv = ["x", "27", "o", "16,18,19"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
Ci = {s for s in S if re.fullmatch(f"[{C}]{{1,2}}i", s)}
z = sc.objective(sc.score(frozenset()))
sets = [("C{1,2}i", Ci), ("C{1,2}i + ky (occuper)", Ci | {"ky"}), ("C{1,2}i + ky + be (obéir)", Ci | {"ky", "be"}),
        ("C{1,2}i + ky + be + ka (occasion)", Ci | {"ky", "be", "ka"}), ("C{1,2}i + ky + be + ka + se (océan)", Ci | {"ky", "be", "ka", "se"}),
        ("C{1,2}i + ky + pe (opération)", Ci | {"ky", "pe"}), ("C{1,2}i + ky + be + ka + pe", Ci | {"ky", "be", "ka", "pe"}), ("ky alone", {"ky"})]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:3]}", flush=True)
