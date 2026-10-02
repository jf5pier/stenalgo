import sys, re
sys.argv = ["x", "26", "rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée", "16,20,21", "rer"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
z = sc.objective(sc.score(frozenset()))
Ce = p(f"[{C}]*e"); P = p("p[aeiouy]")
sets = [("rer alone", set()), ("C*e (é-verbs, = the sweep's list)", Ce), ("p[aeiouy] (préparer, récupérer, respirer)", P), ("p[aeiouy] + sy (assurer)", P | {"sy"}),
        ("p[aeiouy] + sy + ti (tirer)", P | {"sy", "ti"}), ("C*e + pa + pi + sy + ti", Ce | {"pa", "pi", "sy", "ti"}), ("pa + pe", {"pa", "pe"}), ("pa + pe + pi + sy + ti", {"pa", "pe", "pi", "sy", "ti"})]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - (100 if m else 0):+.0f} | {r['fallbackTop'][:3]}", flush=True)
