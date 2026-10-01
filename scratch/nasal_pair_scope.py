"""`@ C{1,2} @`: first syllable sounds @ (any spelling), second syllable = 1-2 consonants + @."""
import pickle, re, sys, collections
sys.path.insert(0, ".")
import src.affixes as A
exec(open("scratch/en_phon_scope.py").read().split("rows = [")[0])
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
anchors = [c for c in cands.values() if c.position == "prefix" and c.k == 1 and c.phono == "@"
           and "|" not in c.ortho and not c.isGeneralized]
print("@ anchors by spelling:", sorted((c.ortho, len(c.carriers)) for c in anchors))
ones, neigh = [], {}
for a in anchors:
    for c in a.carriers:
        syl = c.rec.orthoSylls
        if len(syl) != len(c.rec.base): continue
        j = c.start + c.span
        if j < len(c.rec.phonoSylls):
            ones.append(c); neigh[c.rec.idx] = c.rec.phonoSylls[j]
by = {c.rec.idx: c for c in ones}
rx = re.compile(f"[{C}]{{1,2}}@")
def run(cs): 
    (res,) = A.simulate([(sc.binding, cs)], sc.ctx, boundaryRisk=False); return res
def score(matchOrthoStart):
    cs = [sc.two(c) if (rx.fullmatch(neigh[c.rec.idx]) and matchOrthoStart(c)) else c for c in ones]
    res = run(cs)
    failed = {r.carrier.rec.idx for r in res if r.carrier.span == 2 and r.gain <= 0}
    cs = [by[c.rec.idx] if c.rec.idx in failed else c for c in cs]
    res = run(cs)
    _s, ben, exc, ef, _t = __import__("src.affixrules", fromlist=["x"]).ruleScoreFromResults(res, 0, 1)
    good = [r for r in res if r.carrier.span == 2 and r.gain > 0]
    two = sum(1 for c in cs if c.span == 2)
    return dict(ben=ben, exc=exc, ef=ef, fb=len(failed), gain=len(good), two=two,
                top=[r.carrier.rec.ortho for r in sorted(good, key=lambda r: -r.carrier.rec.frequency)[:12]],
                bySp=collections.Counter(r.carrier.rec.orthoSylls[0] for r in good))
import src.affixrules as RR
obj = lambda r: r["ben"] - RR.EXCEPTION_ALPHA * r["ef"] - 5 * r["fb"] - RR.FORM_COST
print(len(ones), "carriers with first syllable @ and a second syllable")
for label, f in (("no k=2 (anchor-set alone)", lambda c: False), ("only spelled `en`", lambda c: c.rec.orthoSylls[0] == "en"),
                 ("@ C{1,2} @, any spelling of the first @", lambda c: True)):
    r = score(f)
    print(f"{label}: 2-stroke words {r['two']}, really gain {r['gain']}, fallbacks {r['fb']}, benefit {r['ben']:.0f}, hard exc {r['exc']} ({r['ef']:.1f}), objective {obj(r):.0f}")
    if r["gain"]: print("   gaining first syllables:", dict(r["bySp"].most_common(8)), "| top:", r["top"])
