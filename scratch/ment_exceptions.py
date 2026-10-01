import pickle, sys, json
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard()
records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
settings = {"L": (1.0, 5.0, 10.0), "H": (2.0, 150.0, 300.0)}
targets = {"L": ("suffix", 1, "m@", "man|mand|mant|ment|ments|mmant|mment"), "H": ("suffix", 1, "m@", "ment")}
out = {}
for name, (a, e, f) in settings.items():
    R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = a, e, f
    key = targets[name]
    if key not in cands:
        print(name, "key missing; candidates for m@:", [k for k in cands if k[2] == "m@" and k[0] == "suffix"][:10]); continue
    rule = R.buildCandidateRule(cands[key], idx)
    R.chooseRuleKeypress(rule, pk, ctx, keypresses)
    exc = [(r.carrier.rec.ortho, r.carrier.rec.frequency, r.reason) for r in rule.results if r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS]
    exc.sort(key=lambda t: -t[1])
    out[name] = dict(keys=rule.keys, forms=[x.ortho for x in rule.forms], score=rule.score, n=len(exc),
                     freq=sum(t[1] for t in exc), rows=exc,
                     covered=sum(1 for r in rule.results if r.gain > 0), carriers=len(rule.results))
    print(name, rule.keys, len(rule.forms), "forms", len(exc), "exceptions, freq", round(out[name]["freq"], 1), flush=True)
json.dump(out, open("scratch/ment-exceptions.json", "w"), ensure_ascii=False, indent=1, default=list)
