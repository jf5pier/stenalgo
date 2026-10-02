import sys, re, collections
sys.argv = ["x", "10", "té", "19,20,25"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
import src.affixes as A, src.affixrules as RR
C = "ptkbdgfsSvzZmnNlRjw"
syl = {c.rec.idx: c.rec.orthoSylls for c in sc.ones}; ph = {c.rec.idx: c.rec.phonoSylls for c in sc.ones}
def n(c, d):
    j = c.start - d
    return (syl[c.rec.idx][j], ph[c.rec.idx][j]) if j >= 0 else (None, None)
def form(c, k): return c if k == 1 else c._replace(start=c.start - (k - 1), span=k)
def run(cs):
    (res,) = A.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False); return res
def score(assign, forms):
    ks = {c.rec.idx: assign(c) for c in sc.ones}
    res = run([form(c, ks[c.rec.idx]) for c in sc.ones])
    failed = {r.carrier.rec.idx for r in res if r.carrier.span > 1 and r.gain <= 0}
    ks = {i: (1 if i in failed else k) for i, k in ks.items()}
    res = run([form(c, ks[c.rec.idx]) for c in sc.ones])
    _s, ben, exc, ef, _t = RR.ruleScoreFromResults(res, 0, 1)
    kc = collections.Counter(ks.values())
    fb = [c.rec.ortho for c in sorted((c for c in sc.ones if c.rec.idx in failed), key=lambda c: -c.rec.frequency)]
    return ben, exc, ef, len(failed), kc[2], kc[3], RR.EXCEPTION_ALPHA, fb[:5], ben - RR.EXCEPTION_ALPHA * ef - 5 * len(failed) - RR.FORM_COST * forms
r2 = re.compile(f"[{C}]{{1,2}}i")
def isCi(c, d): p = n(c, d)[1]; return bool(p and r2.fullmatch(p))
def k2(c): return isCi(c, 1)
rows = [("tion... té alone", lambda c: 1, 1), ("C{1,2}i (k=2)", lambda c: 2 if k2(c) else 1, 2),
        ("+ k=3: bi|li|té", lambda c: 3 if (k2(c) and n(c, 1)[1] == "li" and n(c, 2)[1] == "bi") else 2 if k2(c) else 1, 3),
        ("+ k=3: any C*i|li|té", lambda c: 3 if (k2(c) and n(c, 1)[1] == "li" and isCi(c, 2)) else 2 if k2(c) else 1, 3),
        ("+ k=3: any Ci|Ci|té", lambda c: 3 if (k2(c) and isCi(c, 2)) else 2 if k2(c) else 1, 3)]
print("| scope | k=2 words | k=3 words | fallbacks | benefit | forms | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, f, forms in rows:
    ben, exc, ef, fb, a, b, _al, top, obj = score(f, forms)
    print(f"| {lab} | {a} | {b} | {fb} | {ben:.0f} | {forms} | {obj:.0f} | {top[:4]}", flush=True)
bil = [c.rec.ortho for c in sc.ones if n(c, 1)[1] == "li" and n(c, 2)[1] == "bi"]
print(len(bil), "words end in bi|li|té:", sorted(set(bil), key=lambda o: -max(c.rec.frequency for c in sc.ones if c.rec.ortho == o))[:8])
