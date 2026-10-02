"""Rank 7 (`ain|hin|im|in`, keys (9,19) after the no-growth `re` rule took (9,18)): growth scopes by the 1-2 syllables after."""
import re, sys, collections, pickle
sys.path.insert(0, ".")
sys.argv = sys.argv[:1]
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402
import src.affixrules as RR  # noqa: E402
import src.affixes as A  # noqa: E402

rule = loadRule(6)
assert rule["root"] == "ain|hin|im|in"
rule["keys"] = [9, 19]
rule["anchors"][0]["anchor"] = "ain|hin|im|in"
sc = Scorer(rule, True, "H")
ones = sc.ones
syl = {c.rec.idx: c.rec.orthoSylls for c in ones}; ph = {c.rec.idx: c.rec.phonoSylls for c in ones}
print(len(ones), "carriers; root", sc.root.ortho, sc.root.phono, "keys", sc.keys, flush=True)
C = "ptkbdgfsSvzZmnNlRjw"
def n(c, d):
    j = c.start + c.span - 1 + d
    return (syl[c.rec.idx][j], ph[c.rec.idx][j]) if j < len(syl[c.rec.idx]) else (None, None)
def form(c, k): return c if k == 1 else c._replace(span=k)
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
    return dict(ben=ben, exc=exc, ef=ef, fb=len(failed), fbF=sum(c.rec.frequency for c in ones if c.rec.idx in failed), fbTop=fb[:5], k2=kc[2], k3=kc[3])
def obj(r, forms): return r["ben"] - RR.EXCEPTION_ALPHA * r["ef"] - 5 * r["fb"] - RR.FORM_COST * forms
L2 = set("bé ce clé cré dé flé fré fé gré gé pe plé pre pré pé quié sai sé te tré té vé".split())
LIM = {"cor", "for", "por"}
L3 = set("ce chi ci cro cu di du fec fen fi for fri gra gre gri li llec lli lo lé ma men mi ni nia nie nieu nio nom nou né o pa pen pi ra re ri ria rieu rio ré sa si ssa ssio te tec ter ti té vi voy".split())
def cur(c):
    a, n1, n2 = syl[c.rec.idx][c.start], n(c, 1)[0], n(c, 2)[0]
    if a == "in" and n1 == "té" and n2 in L3: return 3
    if a == "in" and n1 in L2: return 2
    if a == "im" and n1 in LIM: return 2
    return 1
def pat(rx, first=("in", "im", "ain", "hin")):
    r = re.compile(rx)
    return lambda c: 2 if (syl[c.rec.idx][c.start] in first and n(c, 1)[1] and r.fullmatch(n(c, 1)[1])) else 1
Ce = f"[{C}]*"
scopes = [("anchor alone", lambda c: 1, 1), ("current (in list + im list + inté k=3)", cur, 4),
          ("current minus k=3", lambda c: min(cur(c), 2), 3),
          ("in/im + C*e (k=2)", pat(Ce + "e"), 2), ("in/im + C*[e°] (k=2)", pat(Ce + "[e°]"), 2),
          ("in/im + C*[eE°] (k=2)", pat(Ce + "[eE°]"), 2), ("in/im + any C*V (k=2)", pat(Ce + "[^" + C + "]"), 2)]
print("| scope | k=2 words | k=3 words | fallbacks (freq) | benefit | hard exc (freq) | forms | objective(5) |\n|---|---|---|---|---|---|---|---|")
for label, f, forms in scopes:
    r = score(f)
    print(f"| {label} | {r['k2']} | {r['k3']} | {r['fb']} ({r['fbF']:.0f}) | {r['ben']:.0f} | {r['exc']} ({r['ef']:.1f}) | {forms} | {obj(r, forms):.0f} | {r['fbTop'][:3]}", flush=True)
zero = score(lambda c: 1)
by = collections.defaultdict(list)
for c in ones:
    if syl[c.rec.idx][c.start] in ("in", "im") and n(c, 1)[0]: by[n(c, 1)[0]].append(c)
order = sorted(by, key=lambda s: -sum(c.rec.frequency for c in by[s]))[:22]
print("\nbest single followers of in/im, alone vs anchor alone:")
for s in order:
    r = score(lambda c, s=s: 2 if (syl[c.rec.idx][c.start] in ("in", "im") and n(c, 1)[0] == s) else 1)
    ph1 = collections.Counter(n(c, 1)[1] for c in by[s]).most_common(1)[0][0]
    ex = ", ".join(sorted({c.rec.ortho for c in by[s]}, key=lambda o: -max(c.rec.frequency for c in by[s] if c.rec.ortho == o))[:3])
    print(f"  {s:6} /{ph1}/ words {len(by[s]):3} freq {sum(c.rec.frequency for c in by[s]):7.1f} d_obj {obj(r,2)-obj(zero,1):+6.0f} fb {r['fb']:2} inList {'yes' if s in L2|LIM else 'NO '} {ex}")
