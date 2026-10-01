import sys
exec(open("scratch/ser_scope.py").read().split('rows = [')[0])
FC = 100
def o(r, forms): return r["ben"] - RR.EXCEPTION_ALPHA * r["ef"] - 5 * r["fb"] - FC * forms
sezF = lambda c: isSez(c) and n(c, 1)[1] and cy.fullmatch(n(c, 1)[1])
k3L = lambda c: li(c) and n(c, 2)[0] in L3
rows = [("anchor alone", lambda c: 1, 1),
        ("sez + C*y (k=2)", lambda c: 2 if sezF(c) else 1, 2),
        ("li + ser (k=2)", lambda c: 2 if li(c) else 1, 2),
        ("X + li + ser, X in list (k=3)", lambda c: 3 if k3L(c) else 1, 2),
        ("sez + C*y (k=2) + li+ser (k=2)", lambda c: 2 if (sezF(c) or li(c)) else 1, 3),
        ("sez + C*y (k=2) + X+li+ser list (k=3)", lambda c: 3 if k3L(c) else 2 if sezF(c) else 1, 3),
        ("sez + C*y + X+li+ser list (k=3) + li+ser (k=2) for the rest", lambda c: 3 if k3L(c) else 2 if (sezF(c) or li(c)) else 1, 4)]
print(f"form cost {FC}\n| scope | k=2 words | k=3 words | fallbacks (freq) | benefit | forms | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, f, forms in rows:
    r = score(f)
    print(f"| {lab} | {r['k2']} | {r['k3']} | {r['fb']} ({r['fbF']:.0f}) | {r['ben']:.0f} | {forms} | {o(r, forms):.0f} | {r['top'][:3]}", flush=True)
