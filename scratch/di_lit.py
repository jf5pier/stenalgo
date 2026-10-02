import sys, re
sys.argv = ["x", "24", "de|dea|di|die|dis|dy|dî", "3,16,19", "di"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
S = set(sc.syllables); base = {s for s in S if re.fullmatch(f"[{C}]{{1,2}}i", s)}
sets = [("di alone", set()), ("C{1,2}i", base), ("C{1,2}i + REk (directeur)", base | {"REk"}),
        ("C{1,2}i + REk + vOR (divorcer)", base | {"REk", "vOR"}), ("C{1,2}i + REk + vOR + plo (diplomate)", base | {"REk", "vOR", "plo"})]
print("| scope | phonologies | 2-stroke words | fallbacks (freq) | benefit | objective(5), 1 form charged | net of the growth form (100) |\n|---|---|---|---|---|---|---|")
z = sc.objective(sc.score(frozenset()))
for lab, m in sets:
    r = sc.score(frozenset(m)); o = sc.objective(r)
    print(f"| {lab} | {len(m)} | {r['twoWords']} | {r['fallbacks']} ({r['fallbackFreq']:.0f}) | {r['benefit']:.0f} | {o:.0f} | {o - z - (100 if m else 0):+.0f} |", flush=True)
