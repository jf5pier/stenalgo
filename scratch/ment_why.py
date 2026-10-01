import pickle
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
for name, (a, e, f), key in (("L", (1.0, 5.0, 10.0), ("suffix", 1, "m@", "man|mand|mant|ment|ments|mmant|mment")),
                             ("H", (2.0, 150.0, 300.0), ("suffix", 1, "m@", "ment"))):
    R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = a, e, f
    rule = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(rule, pk, ctx, keypresses)
    tot = sum(r.carrier.rec.frequency for r in rule.results)
    print(f"== {name}: keys {rule.keys}, {len(rule.results)} carriers, total carrier freq {tot:.0f}, "
          f"covered freq {sum(r.carrier.rec.frequency for r in rule.results if r.gain > 0):.0f}")
    # cluster size by new outline among carriers
    bynb = {}
    for r in rule.results:
        if r.reason == "markCostTooHigh" or r.gain > 0:
            pass
    import collections
    print("  moment/allemand/amant/roman under this key:")
    for r in rule.results:
        if r.carrier.rec.ortho in ("moment", "allemand", "amant", "roman", "appartement"):
            print(f"    {r.carrier.rec.ortho:12} base={r.carrier.rec.base} gain={r.gain} reason={r.reason} markCost={r.markCost} "
                  f"partners={[rule.forms[m].ortho[:12] for m in r.partners][:3]}")
    # ending analysis of exceptions
    exc = [r.carrier.rec.ortho for r in rule.results if r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS]
    ends = collections.Counter(o[-3:] if o.endswith("ment") is False else "ment" for o in exc)
    print("  exception endings:", dict(ends.most_common(6)))
