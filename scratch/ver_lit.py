import sys
sys.argv = ["x", "19", "ver", "19,20,22", "vé"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
sets = [("ver alone", []), ("Ri (arrivé)", ["Ri"]), ("Ri + tRu (trouvé)", ["Ri", "tRu"]), ("Ri + tRu + l° (levé, enlevé)", ["Ri", "tRu", "l°"]),
        ("Ri + tRu + l° + zER + ti", ["Ri", "tRu", "l°", "zER", "ti"]), ("current list (20 phonologies)", sorted(curPhon))]
print("| scope | syllables | 2-stroke words | fallbacks (freq) | benefit | objective(5) |\n|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {sc.objective(r):.0f} | {r['fallbackTop'][:3]}", flush=True)
