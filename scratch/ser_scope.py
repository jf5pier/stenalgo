"""Rank 23 (`ser|sée|zer|zé`, keys (16,19,20)): -liser (k=3: X + li + ser) and -usez (k=2: Cy + sez), scored jointly."""
import re, sys, collections
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402
import src.affixrules as RR, src.affixes as A  # noqa: E402
rule = loadRule(23); assert rule["root"] == "ser|sée|zer|zé"
rule["keys"] = [16, 19, 20]; rule["anchors"][0]["anchor"] = rule["root"]
sc = Scorer(rule, True, "H"); ones = sc.ones
syl = {c.rec.idx: c.rec.orthoSylls for c in ones}; ph = {c.rec.idx: c.rec.phonoSylls for c in ones}
C = "ptkbdgfsSvzZmnNlRjw"
def n(c, d):
    j = c.start - d
    return (syl[c.rec.idx][j], ph[c.rec.idx][j]) if j >= 0 else (None, None)
def form(c, k): return c if k == 1 else c._replace(start=c.start - (k - 1), span=k)
def run(cs):
    (res,) = A.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False); return res
def score(assign):
    ks = {c.rec.idx: assign(c) for c in ones}
    res = run([form(c, ks[c.rec.idx]) for c in ones])
    failed = {r.carrier.rec.idx for r in res if r.carrier.span > 1 and r.gain <= 0}
    ks = {i: (1 if i in failed else k) for i, k in ks.items()}
    res = run([form(c, ks[c.rec.idx]) for c in ones])
    _s, ben, exc, ef, _t = RR.ruleScoreFromResults(res, 0, 1)
    kc = collections.Counter(ks.values())
    fb = [c.rec.ortho for c in sorted((c for c in ones if c.rec.idx in failed), key=lambda c: -c.rec.frequency)]
    return dict(ben=ben, exc=exc, ef=ef, fb=len(failed), fbF=sum(c.rec.frequency for c in ones if c.rec.idx in failed), top=fb[:4], k2=kc[2], k3=kc[3])
def obj(r, forms): return r["ben"] - RR.EXCEPTION_ALPHA * r["ef"] - 5 * r["fb"] - RR.FORM_COST * forms
L3 = set()
for a in rule["anchors"]:
    if a["k"] == 3:
        for grp in re.findall(r"\[(.*?)\]", a["form"]): L3 |= set(grp.split("|"))
print(len(ones), "carriers;", len(L3), "syllables in the sweep's k=3 list", flush=True)
cy = re.compile(f"[{C}]*y"); cv = re.compile(f"[{C}]*[^{C}]")
isSez = lambda c: syl[c.rec.idx][c.start] == "sez"
li = lambda c: n(c, 1)[1] == "li"
rows = [("anchor alone", lambda c: 1, 1),
        ("k=2: sez + C*y (excusez, refusez)", lambda c: 2 if (isSez(c) and n(c, 1)[1] and cy.fullmatch(n(c, 1)[1])) else 1, 2),
        ("k=3: li + any previous syllable", lambda c: 3 if (li(c) and n(c, 2)[1]) else 1, 2),
        ("k=3: li + previous in the sweep's list", lambda c: 3 if (li(c) and n(c, 2)[0] in L3) else 1, 2),
        ("k=3: li + previous C*V (single vowel)", lambda c: 3 if (li(c) and n(c, 2)[1] and cv.fullmatch(n(c, 2)[1])) else 1, 2),
        ("k=2: li + ser (just -liser, no 3rd syllable)", lambda c: 2 if li(c) else 1, 2)]
print("| scope | k=2 words | k=3 words | fallbacks (freq) | benefit | forms | objective(5) |\n|---|---|---|---|---|---|---|")
for lab, f, forms in rows:
    r = score(f)
    print(f"| {lab} | {r['k2']} | {r['k3']} | {r['fb']} ({r['fbF']:.0f}) | {r['ben']:.0f} | {forms} | {obj(r, forms):.0f} | {r['top']}", flush=True)
