import sys
sys.argv = ["x", "15", "ai|aî|e|ei|hai|he|hê|é", "5,18,19"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
sc.neigh = {i: f"{first[i]}:{phon[i]}" for i in phon}; sc.syllables = sorted(set(sc.neigh.values())); sc.cache = {}
E = ["e:ksky", "e:kspli", "e:sE", "e:n°"]
sets = [("anchor alone", []), ("e: ksky kspli sE n°", E), ("ai: m° only", ["ai:m°"]), ("e: four literals + ai: m°", E + ["ai:m°"]),
        ("e: four literals + ai: m° + d°", E + ["ai:m°", "ai:d°"])]
print("| scope | 2-stroke words | fallbacks (freq) | benefit | hard exc | objective(5) |\n|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {r['exc']} | {sc.objective(r):.0f} | {r['fallbackTop'][:3]}", flush=True)
