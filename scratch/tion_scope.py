"""Rank 6 (`-tion`, keys (9,20,25)): scopes of the 2- and 3-syllable forms by the PHONOLOGY of the 1-2 syllables before `tion`."""
import re, sys, collections
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402
import src.affixrules as RR  # noqa: E402

rule = loadRule(7)
assert rule["root"] == "tion"
sc = Scorer(rule, True, "H")
ones = [c for c in sc.ones]
syl = {c.rec.idx: c.rec.orthoSylls for c in ones}
ph = {c.rec.idx: c.rec.phonoSylls for c in ones}
print(len(ones), "carriers; root", sc.root.ortho, sc.root.phono, flush=True)
C = "ptkbdgfsSvzZmnNlRjw"
def n(c, d):            # d-th syllable before the anchor syllable (1 = right before)
    j = c.start - d
    return (syl[c.rec.idx][j], ph[c.rec.idx][j]) if j >= 0 else (None, None)
def form(c, k):
    return c if k == 1 else c._replace(start=c.start - (k - 1), span=k)
def run(cs):
    (res,) = RR.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False) if hasattr(RR, "simulate") else __import__("src.affixes", fromlist=["x"]).simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False)
    return res
def score(assign):      # assign(c) -> 1/2/3
    ks = {c.rec.idx: assign(c) for c in ones}
    cs = [form(c, ks[c.rec.idx]) for c in ones]
    res = run(cs)
    failed = {r.carrier.rec.idx for r in res if r.carrier.span > 1 and r.gain <= 0}
    ks = {i: (1 if i in failed else k) for i, k in ks.items()}
    cs = [form(c, ks[c.rec.idx]) for c in ones]
    res = run(cs)
    _s, ben, exc, ef, _t = RR.ruleScoreFromResults(res, 0, 1)
    kinds = collections.Counter(ks.values())
    fb = [c.rec.ortho for c in sorted((c for c in ones if c.rec.idx in failed), key=lambda c: -c.rec.frequency)]
    return dict(ben=ben, exc=exc, ef=ef, fb=len(failed), fbTop=fb[:6], fbFreq=sum(c.rec.frequency for c in ones if c.rec.idx in failed),
                k2=kinds[2], k3=kinds[3], two=sum(1 for c in ones if ks[c.rec.idx] > 1))
def obj(r, forms): return r["ben"] - RR.EXCEPTION_ALPHA * r["ef"] - 5 * r["fb"] - RR.FORM_COST * forms
Ca = re.compile(f"[{C}]*a"); Ci = re.compile(f"[{C}]*i")
def isCa(c): p = n(c, 1)[1]; return bool(p and Ca.fullmatch(p))
def isCi2(c): p = n(c, 2)[1]; return bool(p and Ci.fullmatch(p))
TEN = {"sten", "ten", "tten", "ven"}
def isTen(c): return n(c, 1)[0] in TEN
scopes = [
 ("tion alone (k=1)", lambda c: 1, 1),
 ("+ Ca (k=2)", lambda c: 2 if isCa(c) else 1, 2),
 ("+ ten/ven/tten (k=2)", lambda c: 2 if isTen(c) else 1, 2),
 ("Ca (k=2) + ten/ven/tten", lambda c: 2 if (isCa(c) or isTen(c)) else 1, 3),
 ("Ca (k=2) + Ci Ca (k=3)", lambda c: 3 if (isCa(c) and isCi2(c)) else 2 if isCa(c) else 1, 3),
 ("Ca (k=2) + Ci Ca (k=3) + ten/ven/tten", lambda c: 3 if (isCa(c) and isCi2(c)) else 2 if (isCa(c) or isTen(c)) else 1, 4),
]
print("| scope | k=2 words | k=3 words | fallbacks (freq) | benefit | hard exc (freq) | forms | objective(5) |\n|---|---|---|---|---|---|---|---|")
for label, f, forms in scopes:
    r = score(f)
    print(f"| {label} | {r['k2']} | {r['k3']} | {r['fb']} ({r['fbFreq']:.0f}) | {r['ben']:.0f} | {r['exc']} ({r['ef']:.1f}) | {forms} | {obj(r, forms):.0f} |  {r['fbTop'][:4]}", flush=True)

print("\nk=2 vowel-class variants (tion k=1 + one k=2 form), forms=2:")
def v(rx):
    r = re.compile(f"[{C}]*({rx})")
    return lambda c: 2 if (n(c, 1)[1] and r.fullmatch(n(c, 1)[1])) else 1
for label, rx in (("C*a", "a"), ("C+a (a alone excluded)", None), ("C*[ai]", "a|i"), ("C*[ae]", "a|e|E"), ("C*[ao]", "a|o|O"), ("C*[aeio...] any single vowel", "[^" + C + "]")):
    if rx is None:
        r0 = re.compile(f"[{C}]+a"); f = lambda c: 2 if (n(c, 1)[1] and r0.fullmatch(n(c, 1)[1])) else 1
    else:
        f = v(rx)
    r = score(f)
    print(f"| {label} | k2 {r['k2']} | fb {r['fb']} ({r['fbFreq']:.0f}) | benefit {r['ben']:.0f} | exc {r['exc']} ({r['ef']:.1f}) | obj {obj(r, 2):.0f} | {r['fbTop'][:4]}", flush=True)
