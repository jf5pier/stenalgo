import sys, re, collections
sys.argv = ["x", "15", "ai|aî|e|ei|hai|he|hê|é", "5,18,19", "e"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables)
def p(rx): return {s for s in S if re.fullmatch(rx, s)}
ks = p("ks.*")
lit = {"sE", "n°"}
sets = [("e alone", set()), ("current list", set(curPhon)),
        ("ks.* (neighbour starts with ks = spelled x)", ks),
        ("ks.* minus kst.* (extra...)", {s for s in ks if not s.startswith("kst")}),
        ("ks.* minus kst.* + sE + n°", {s for s in ks if not s.startswith("kst")} | lit),
        ("ks.* + sE + n°", ks | lit),
        ("ks.* minus kst.* minus ksplik/kskyz-like (…z/…k endings)", {s for s in ks if not s.startswith("kst") and not re.fullmatch("ks.*[zkt]", s)}),
        ("ks.* minus kst.* minus …z/…k endings + sE + n°", {s for s in ks if not s.startswith("kst") and not re.fullmatch("ks.*[zkt]", s)} | lit)]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {sc.objective(r):.0f} | {r['fallbackTop'][:4]}", flush=True)
