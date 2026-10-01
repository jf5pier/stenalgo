"""Growth check for the UNAPPROVED spellings of a fusion (fusion_check.py): approved forms kept, then each
neighbour syllable (by sound) of the added spellings scored on its own (marginal objective vs anchor only, net of a 100 form).
Usage: env/bin/python scratch/fusion_growth.py POS 'MERGED_ORTHO' PHONO KEYS   e.g. prefix 'am|an|ant|em|en|ench|enh|ham|han|hen' @ 3,6,18"""
import collections, pickle, re, sys
sys.path.insert(0, ".")
pos, mortho, mphono, keys = sys.argv[1], sys.argv[2], sys.argv[3], tuple(int(k) for k in sys.argv[4].split(","))
sys.argv = sys.argv[:1]
from src import affixes as A, affixrules as R
from src.affixes import Binding, RULE, simulate
from src.affixscopes import SCOPES
from util import affix_scan as S
A.RULE_PARTIAL_OVERLAP = True
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == "D")
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
pool = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, *_ = S._engine(pool, records, starboard)
byKey = {(c.position, c.k, c.phono, c.ortho): c for c in pool.values()}
M = next(c for c in pool.values() if c.position == pos and c.k == 1 and c.ortho == mortho and c.phono == mphono)
key = lambda c: (c.position, c.ortho, c.phono)
approvedParts = [byKey[k] for k in M.mergeParts if k in byKey and key(byKey[k]) in SCOPES]
idx = R.childrenIndex(pool)
forms = [c for x in approvedParts for c in R.descendantsOf(x, idx) if c.isScoped]
approvedGrown = {c.rec.idx: c for f in forms for c in f.carriers}
suffix = pos == "suffix"
ones = []
for c in M.carriers:
    r = c.rec
    if len(r.orthoSylls) != len(r.base): continue
    ones.append((c, A._growCarrier(pos, c)))   # g is None when no neighbour/stem is left: anchor only
binding = Binding(pos, RULE, keys)
def run(assign):                              # assign: idx -> grown carrier or None
    cs = [assign.get(c.rec.idx, c) for c, _ in ones]
    (res,) = simulate([(binding, cs)], ctx, boundaryRisk=False)
    failed = {r.carrier.rec.idx for r in res if r.carrier.span > 1 and r.gain <= 0}
    if failed:
        cs = [c if c.rec.idx in failed else assign.get(c.rec.idx, c) for c, _ in ones]
        cs = [next(o for o, _ in ones if o.rec.idx == x.rec.idx) if x.rec.idx in failed else x for x in cs]
        (res,) = simulate([(binding, cs)], ctx, boundaryRisk=False)
    _s, ben, exc, ef, _t = R.ruleScoreFromResults(res, 0, 1)
    return ben - R.EXCEPTION_ALPHA * ef - 5 * len(failed), len(failed), exc, ef
inOnes = {c.rec.idx for c, _ in ones}
base = {i: g for i, g in approvedGrown.items() if i in inOnes}
o0 = run(base)
print(f"{len(ones)} carriers; approved-forms-only objective {o0[0]:.0f} (fb {o0[1]}, exc {o0[2]}/{o0[3]:.0f}); keys {keys}")
newC = [(c, g) for c, g in ones if g is not None and c.rec.idx not in approvedGrown]
bySyll = collections.defaultdict(list)
for c, (gc, ph, orth) in newC:
    bySyll[(c.rec.orthoSylls[c.start], ph)].append((c, gc, orth))
fq = lambda lst: sum(c.rec.frequency for c, _, _ in lst)
anchors = collections.Counter(c.rec.orthoSylls[c.start] for c, _ in newC)
print("added spellings:", dict(anchors.most_common()))
rows = []
for (a, ph), lst in bySyll.items():
    if len(lst) < 3: continue
    o = run({**base, **{c.rec.idx: gc for c, gc, _ in lst}})
    rows.append((o[0] - o0[0] - 100, a, ph, len(lst), fq(lst), o[1], [c.rec.ortho for c, _, _ in sorted(lst, key=lambda t: -t[0].rec.frequency)[:4]]))
rows.sort(key=lambda r: -r[0])
print("best single (anchor spelling, neighbour sound), net of a 100 form, >=3 words:")
for d, a, ph, n, f, fb, ex in rows[:25]:
    print(f"  {a:4} + /{ph}/ words {n:4} freq {f:6.1f} d_obj {d:+6.0f} fb {fb:3} {' '.join(ex)}")

print("\napproved forms' own patterns applied to each added anchor spelling (net of a 100 form):")
for x in approvedParts:
    for f in SCOPES[key(x)]:
        for a in [a for a, n in anchors.most_common() if n >= 3]:
            lst = [(c, gc) for c, (gc, ph, orth) in newC if c.rec.orthoSylls[c.start] == a and (f.sound is None or f.sound.fullmatch(ph)) and (f.spelling is None or f.spelling.fullmatch(orth))] if (f.sound is not None or f.spelling is not None) else []
            if not lst: continue
            o = run({**base, **{c.rec.idx: gc for c, gc in lst}})
            print(f"  {x.ortho}:{f.label} on `{a}`: words {len(lst):4} d_obj {o[0] - o0[0] - 100:+6.0f} fb {o[1]} examples {' '.join(c.rec.ortho for c, _ in lst[:5])}")
