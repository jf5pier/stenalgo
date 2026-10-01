import sys, re
sys.argv = ["x", "10", "té", "19,20,25"]
exec(open("scratch/phon_scope.py").read().split('vowels = sorted')[0])
import src.affixes as A, src.affixrules as RR
def sel(ex):
    cls = "[" + "".join(c for c in C if c not in ex) + "]"
    r = re.compile(cls + "{1,2}i"); return frozenset(s for s in sc.syllables if r.fullmatch(s))
def excs(m):
    cs = [sc.two(c) if sc.neigh[c.rec.idx] in m else c for c in sc.ones]
    (res,) = A.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False)
    failed = {r.carrier.rec.idx for r in res if r.carrier.span == 2 and r.gain <= 0}
    cs = [sc.byIdx[c.rec.idx] if c.rec.idx in failed else c for c in cs]
    (res,) = A.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False)
    return {r.carrier.rec.ortho: (r.reason, r.carrier.span) for r in res if r.reason in RR.WORD_EXCEPTION_REASONS}
a, b = excs(sel("b")), excs(sel("bv"))
print(len(a), len(b))
print("only with /b/ excluded:", {k: v for k, v in a.items() if k not in b})
print("only with /b/ and /v/ excluded:", {k: v for k, v in b.items() if k not in a})
print("(both)", sorted(set(a) & set(b))[:12], "...")
