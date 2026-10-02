import sys, itertools, re
sys.argv = ["x", "10", "té", "19,20,25"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
cons = sorted({ch for s in sc.syllables for ch in s if ch in C})
def sel(ex):
    cls = "[" + "".join(c for c in C if c not in ex) + "]"
    r = re.compile(cls + "{1,2}i"); return frozenset(s for s in sc.syllables if r.fullmatch(s))
base = sc.score(sel(()))
print(f"C{{1,2}}i: fallbacks {base['fallbacks']} ({base['fallbackFreq']:.0f}), benefit {base['benefit']:.0f}, hard exc {base['exc']}, objective {sc.objective(base):.0f}")
rows = []
for k in (1, 2, 3):
    for ex in itertools.combinations(cons, k):
        m = sel(ex); r = sc.score(m); rows.append((k, "".join(ex), r))
print("\nsingle exclusions (sorted by fallbacks):")
for k, ex, r in sorted([x for x in rows if x[0] == 1], key=lambda x: x[2]["fallbacks"])[:10]:
    print(f"  \\{{{ex}}}: fallbacks {r['fallbacks']:3} ({r['fallbackFreq']:.0f}) benefit {r['benefit']:.0f} hard exc {r['exc']} obj {sc.objective(r):.0f}")
for k in (2, 3):
    print(f"\nbest {k}-letter exclusions by objective, then by fewest fallbacks:")
    seen = set()
    for _k, ex, r in sorted([x for x in rows if x[0] == k], key=lambda x: -sc.objective(x[2])):
        key = (round(sc.objective(r)), r["fallbacks"])
        if key in seen: continue
        seen.add(key)
        print(f"  \\{{{ex}}}: fallbacks {r['fallbacks']:3} ({r['fallbackFreq']:.0f}) benefit {r['benefit']:.0f} hard exc {r['exc']} obj {sc.objective(r):.0f}")
        if len(seen) >= 5: break
best = min(rows, key=lambda x: x[2]["fallbacks"])
print("\nfewest fallbacks of all:", best[1], best[2]["fallbacks"], "obj", round(sc.objective(best[2])), "benefit", round(best[2]["benefit"]))
r = best[2]; print("top fallbacks of C{1,2}i plain:", base["fallbackTop"])
