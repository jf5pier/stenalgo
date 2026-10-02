import sys
sys.argv = ["x", "16", "der", "16,19,25", "dez"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
sets = [("der alone", []), ("gaR (regardez, gardez)", ["gaR"]), ("gaR + m@ (demandez, commandez)", ["gaR", "m@"]),
        ("gaR + m@ + kOR + si", ["gaR", "m@", "kOR", "si"]), ("current list (29 phonologies)", sorted(curPhon))]
print("| scope | syllables | 2-stroke words | fallbacks (freq) | benefit | objective(5) |\n|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {sc.objective(r):.0f} | {r['fallbackTop'][:3]}", flush=True)
