"""For each H rule: exception kinds, and whether a first-stroke key condition (scope rule) explains the physical ones."""
import csv, pickle, collections, json
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = 2.0, 150.0, 300.0
byOrtho = {}
for k, c in cands.items():
    if c.isAnchor and c.k == 1: byOrtho.setdefault((c.position, c.ortho), []).append(k)
rows = list(csv.DictReader(open("scratch/affix-sweep/H/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
def nk(pos, c):
    base = c.rec.base
    ni = c.start + c.span if pos == "prefix" else c.start - 1
    return frozenset(base[ni]) if 0 <= ni < len(base) else frozenset()
isExc = lambda r: r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS
out = []
for row in rows:
    rule = None
    for key in byOrtho.get((row["position"], row["root"]), []):
        r = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(r, pk, ctx, keypresses)
        if len(r.results) == int(row["carriers"]) and r.wordExceptions == int(row["wordExceptions"]): rule = r; break
    if rule is None: print("NO MATCH", row["root"], flush=True); continue
    pos = rule.position
    res = rule.results
    exc = [r for r in res if isExc(r)]
    trap = [r for r in exc if r.reason == "standaloneTrap"]
    other = [r for r in exc if r.reason != "standaloneTrap"]
    # keys that (almost) always fail: >= 90% of the carriers whose neighbour stroke has the key are traps, >= 2 trap words
    have, failed = collections.Counter(), collections.Counter()
    for r in res:
        for k in nk(pos, r.carrier):
            have[k] += 1
            if r.reason == "standaloneTrap" and isExc(r): failed[k] += 1
    K = sorted(k for k in have if failed[k] >= 2 and failed[k] / have[k] >= 0.9)
    inScope = lambda r: not (nk(pos, r.carrier) & set(K))
    excl = [r for r in res if not inScope(r)]
    coveredTrap = [r for r in trap if not inScope(r)]
    collateral = [r for r in excl if r.gain > 0]
    residual = [r for r in exc if inScope(r)]
    fq = lambda rs: sum(r.carrier.rec.frequency for r in rs)
    sv = lambda rs: sum(r.carrier.rec.frequency * r.gain for r in rs if r.gain > 0)
    d = dict(rank=int(row["rank"]), rule=f"{pos} {row['root'][:28]}", keys=rule.keys, words=len(res), exc=len(exc), excF=fq(exc), trap=len(trap), trapF=fq(trap),
             other=len(other), otherF=fq(other), K=K, kw=len(excl), coveredTrap=len(coveredTrap), collateral=len(collateral), collateralSaving=sv(collateral),
             residual=len(residual), residualF=fq(residual), saving=sv(res))
    out.append(d)
    print(f"{d['rank']:2} {d['rule']:32} words {d['words']:5} exc {d['exc']:4}/{d['excF']:6.0f} = trap {d['trap']:4}/{d['trapF']:6.0f} + collision {d['other']:4}/{d['otherF']:6.0f} | scope excl keys {K} -> {d['kw']} words out, "
          f"{d['coveredTrap']} traps covered, {d['collateral']} gainers lost (saving {d['collateralSaving']:.0f} of {d['saving']:.0f}), residual exc {d['residual']}/{d['residualF']:.0f}", flush=True)
json.dump(out, open("scratch/scope-prune.json", "w"), default=list, ensure_ascii=False, indent=1)
