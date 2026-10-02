import csv, pickle, json
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
byOrtho = {}
for k, c in cands.items():
    if c.isAnchor and c.k == 1:
        byOrtho.setdefault((c.position, c.ortho), []).append(k)
out = {}
for name, (a, e, f) in (("L", (1.0, 5.0, 10.0)), ("M", (1.0, 50.0, 100.0)), ("H", (2.0, 150.0, 300.0))):
    R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = a, e, f
    rows = list(csv.DictReader(open(f"scratch/affix-sweep/{name}/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
    res = []
    for row in rows:
        keys = byOrtho.get((row["position"], row["root"]), [])
        best = None
        for key in keys:
            rule = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(rule, pk, ctx, keypresses)
            if len(rule.results) == int(row["carriers"]) and rule.wordExceptions == int(row["wordExceptions"]):
                best = rule; break
        if best is None:
            res.append(dict(rank=int(row["rank"]), position=row["position"], root=row["root"], match=False)); print(name, row["rank"], row["root"], "NO MATCH", flush=True); continue
        cov = [r for r in best.results if r.gain > 0]
        exc = [r for r in best.results if r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS]
        oth = [r for r in best.results if r.gain <= 0 and r.reason not in R.WORD_EXCEPTION_REASONS]
        fq = lambda rs: sum(r.carrier.rec.frequency for r in rs)
        res.append(dict(rank=int(row["rank"]), position=row["position"], root=row["root"], match=True, forms=len(best.forms),
                        covW=len(cov), covF=fq(cov), excW=len(exc), excF=fq(exc), othW=len(oth), othF=fq(oth),
                        saved=float(row["strokeFreqSaved"]), score=float(row["score"])))
        print(name, row["rank"], row["root"][:30], res[-1]["covW"], round(res[-1]["covF"]), res[-1]["excW"], round(res[-1]["excF"]), flush=True)
    out[name] = res
json.dump(out, open("scratch/coverage-exceptions.json", "w"), ensure_ascii=False, indent=1)
