import csv, pickle, collections
from src import affixrules as R
from src.affixes import Binding, RULE, poolCarriers, _newBase
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = 2.0, 150.0, 300.0
row = next(r for r in csv.DictReader(open("scratch/affix-sweep/H/affix-rules.tsv", encoding="utf-8"), delimiter="\t") if r["position"] == "prefix" and r["root"] == "en")
rule = None
for key in [k for k, c in cands.items() if c.isAnchor and c.k == 1 and c.position == "prefix" and c.ortho == "en"]:
    r = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(r, pk, ctx, keypresses)
    if len(r.results) == int(row["carriers"]) and r.wordExceptions == int(row["wordExceptions"]): rule = r; break
A = rule.keys; B = (19,); CLS = {14, 25, 18, 22}
part = lambda k: ctx._partOf.get(k, "?")
print("forms:", [f.ortho[:50] for f in rule.forms], "| rule key A", A, [part(k) for k in A], "phono of root", rule.root.phono)
nk = lambda c: frozenset(c.rec.base[c.start + c.span]) if c.start + c.span < len(c.rec.base) else frozenset()
def why(c, keys):
    n = nk(c)
    if not n: return "noNeighbour"
    if n & set(keys): return "keyOverlap"
    if not ctx.isLegal(tuple(sorted(n | set(keys)))): return "illegalChord"
    return "ok"
isExc = lambda r: r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS
exc = [r for r in rule.results if isExc(r)]
print("\nWHY the 134 exceptions fail under key A:", collections.Counter(why(r.carrier, A) for r in exc))
print("first-stroke keys of exceptions by kind:")
for kind in ("keyOverlap", "illegalChord"):
    ks = collections.Counter(k for r in exc if why(r.carrier, A) == kind for k in nk(r.carrier))
    print(" ", kind, {f"{k}/{part(k)[0]}": n for k, n in ks.most_common(8)})
    print("   e.g.", [r.carrier.rec.ortho for r in sorted((r for r in exc if why(r.carrier, A) == kind), key=lambda r: -r.carrier.rec.frequency)[:8]])
carr = poolCarriers(rule.forms)
fq = lambda rs: sum(r.carrier.rec.frequency for r in rs)
base = sum(r.carrier.rec.frequency * r.gain for r in rule.results if r.gain > 0)
print(f"baseline key A {A}: {len(rule.results)} words, exceptions {len(exc)} / {fq(exc):.1f} freq, saving {base:.0f}")
for CLS in ({18, 22}, {18, 22, 25}, {14, 18, 22, 25}):
    Bset = [c for c in carr if nk(c) & CLS]; Aset = [c for c in carr if not (nk(c) & CLS)]
    (resA,) = R.simulate([(Binding("prefix", RULE, A), Aset)], ctx, boundaryRisk=False)
    (resB,) = R.simulate([(Binding("prefix", RULE, B), Bset)], ctx, boundaryRisk=False)
    e = [r for r in resA + resB if isExc(r)]
    sv = sum(r.carrier.rec.frequency * r.gain for r in resA + resB if r.gain > 0)
    print(f"class B = first stroke has {sorted(CLS)}: B {len(Bset)} words / A {len(Aset)} words; exceptions A {sum(1 for r in resA if isExc(r))}, B {sum(1 for r in resB if isExc(r))}; total {len(e)} words / {fq(e):.1f} freq; saving {sv:.0f}")
