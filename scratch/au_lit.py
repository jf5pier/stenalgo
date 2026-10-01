import sys
sys.argv = ["x", "11", "au", "2,5,8"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
import collections
fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
ex = collections.defaultdict(list)
for c in sc.ones: ex[sc.neigh[c.rec.idx]].append(c.rec.ortho)
sets = [("au alone", []), ("ZuR (aujourd'hui)", ["ZuR"]), ("to (auto-, autorité)", ["to"]), ("ZuR + to", ["ZuR", "to"]),
        ("ZuR + to + tR° (autrement, autrefois)", ["ZuR", "to", "tR°"]), ("ZuR + to + tR° + di (audition)", ["ZuR", "to", "tR°", "di"]),
        ("to + tR°", ["to", "tR°"]), ("current list (29 phonologies)", sorted(curPhon))]
print("| scope | syllables | 2-stroke words | fallbacks (freq) | benefit | objective(5) |\n|---|---|---|---|---|---|")
for lab, m in sets:
    r = sc.score(frozenset(m))
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {sc.objective(r):.0f} |", flush=True)
print("to words:", sorted(set(ex["to"]))[:12], "...", len(set(ex["to"])))
print("ZuR words:", sorted(set(ex["ZuR"])), "tR°:", sorted(set(ex["tR°"])))
