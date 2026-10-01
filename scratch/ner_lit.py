import sys, re
sys.argv = ["x", "29", "ner", "18,19,20", "né"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
z = sc.objective(sc.score(frozenset()))
Ci = p(f"[{C}]{{1,2}}i")
sets = [("m[i°] (terminé, ramené)", p("m[i°]")), ("mi alone", {"mi"}), ("m[i°] + si (dessiné)", p("m[i°]") | {"si"}), ("m[i°] + si + fo + da", p("m[i°]") | {"si", "fo", "da"}),
        ("m[i°] + C{1,2}i", p("m[i°]") | Ci), ("C{1,2}i", Ci), ("[ms]i + m°", p("[ms]i") | {"m°"}), ("current list (48)", set(curPhon))]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5) | net of a 100 form |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - 100:+.0f} | {r['fallbackTop'][:3]}", flush=True)
