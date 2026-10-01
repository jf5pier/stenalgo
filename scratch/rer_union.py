import sys, re
sys.argv = ["x", "26", "rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée", "16,20,21", "rer"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
z = sc.objective(sc.score(frozenset()))
Ce = p(f"[{C}]*e"); P = p("p[aeiouy]")
sets = [("C*e", Ce), ("p[aeiouy]", P), ("p[aeiouy] + C*e", P | Ce), ("p[aeiouy] + C*e + sy", P | Ce | {"sy"}),
        ("p[aeiouy] + C{1,2}e (no empty onset)", P | p(f"[{C}]{{1,2}}e"))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:4]}", flush=True)
print("C*e phonologies:", sorted(Ce))
