import sys
sys.argv = ["x", "15", "ai|aî|e|ei|hai|he|hê|é", "5,18,19", "e"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
sets = [("e alone", []), ("sE (essayer)", ["sE"]), ("sE + n° (ennemi)", ["sE", "n°"]), ("sE + n° + ksE (excellent)", ["sE", "n°", "ksE"]),
        ("ksky + kspli + kspe + ksplo (excuser, expliquer, expérience, exploser)", ["ksky", "kspli", "kspe", "ksplo"]),
        ("sE + n° + ksE + ksky + kspli + kspe + ksplo", ["sE", "n°", "ksE", "ksky", "kspli", "kspe", "ksplo"]),
        ("ksky + kspli + sE + n°", ["ksky", "kspli", "sE", "n°"]),
        ("current list (11)", sorted(curPhon))]
print("| e-form scope | syllables | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {sc.objective(r):.0f} | {r['fallbackTop'][:3]}", flush=True)
