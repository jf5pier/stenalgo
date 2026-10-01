import sys, itertools, re
sys.argv = ["x", "10", "té", "19,20,25"]
src = open("scratch/phon_scope.py").read().split('vowels = sorted')[0]
exec(src)
cons = sorted({ch for s in sc.syllables for ch in s if ch in C})
def sel(onsetRx, vowel):
    r = re.compile(onsetRx + vowel); return frozenset(s for s in sc.syllables if r.fullmatch(s))
res = []
for onset in ("{1,2}", "*"):
    for k in (0, 1, 2):
        for ex in itertools.combinations(cons, k):
            cls = "[" + "".join(c for c in C if c not in ex) + "]"
            for vow in ("i", "[ai]"):
                m = sel(cls + onset, vow)
                if not m: continue
                r = sc.score(m)
                res.append((sc.objective(r), f"C{'' if not ex else chr(92)+'{'+''.join(ex)+'}'}{onset}{vow}", len(m), r))
res.sort(key=lambda x: -x[0])
print("best scopes (objective(5)); list = 3261, anchor alone = 2678")
seen = set()
for o, lab, n, r in res:
    key = (round(o), r["twoWords"])
    if key in seen: continue
    seen.add(key)
    print(f"{lab:22} phon {n:2} 2-stroke {r['twoWords']:4} fallbacks {r['fallbacks']:3} ({r['fallbackFreq']:.0f}) benefit {r['benefit']:.0f} exc {r['exc']} obj {o:.0f}")
    if len(seen) >= 12: break

print("\nsimpler variants:")
for lab, onset, ex, vow in (("C{1,2}i", "{1,2}", "", "i"), ("C*i", "*", "", "i"), ("C\\{b}{1,2}i", "{1,2}", "b", "i"), ("C\\{v}{1,2}i", "{1,2}", "v", "i"), ("C\\{bv}{1,2}i", "{1,2}", "bv", "i"), ("C\\{b}*i", "*", "b", "i")):
    cls = "[" + "".join(c for c in C if c not in ex) + "]"
    m = sel(cls + onset, vow); r = sc.score(m)
    print(f"{lab:16} phon {len(m):2} 2-stroke {r['twoWords']:4} fallbacks {r['fallbacks']:3} ({r['fallbackFreq']:.0f}) benefit {r['benefit']:.0f} exc {r['exc']} ({r['excFreq']:.1f}) obj {sc.objective(r):.0f} {r['fallbackTop'][:5]}")
