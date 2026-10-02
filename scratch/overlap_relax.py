"""What if a PARTIAL key overlap is allowed (only fail when ALL the rule's keys are already in the stem stroke)?"""
import csv, inspect, pickle, collections
import src.affixes as A
from src import affixrules as R
from src.affixes import Binding, RULE, poolCarriers
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = 2.0, 150.0, 300.0
orig = A._newBase
src = inspect.getsource(orig).replace("if set(neighbour) & set(binding.keys):", "if set(binding.keys) <= set(neighbour):")
assert src != inspect.getsource(orig)
ns = dict(vars(A)); exec(src, ns); relaxed = ns["_newBase"]
rows = list(csv.DictReader(open("scratch/affix-sweep/H/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
byOrtho = {}
for k, c in cands.items():
    if c.isAnchor and c.k == 1: byOrtho.setdefault((c.position, c.ortho), []).append(k)
isExc = lambda r: r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS
fq = lambda rs: sum(r.carrier.rec.frequency for r in rs)
sv = lambda rs: sum(r.carrier.rec.frequency * r.gain for r in rs if r.gain > 0)
tot = collections.Counter()
for row in rows:
    if len(eval(row["keys"])) < 2 if row["keys"].startswith("(") else True: continue
    rule = None
    for key in byOrtho.get((row["position"], row["root"]), []):
        r = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(r, pk, ctx, keypresses)
        if len(r.results) == int(row["carriers"]) and r.wordExceptions == int(row["wordExceptions"]): rule = r; break
    if rule is None: continue
    carriers = poolCarriers(rule.forms)
    e0 = [r for r in rule.results if isExc(r)]
    A._newBase = relaxed
    try: (res,) = R.simulate([(Binding(rule.position, RULE, rule.keys), carriers)], ctx, boundaryRisk=False)
    finally: A._newBase = orig
    e1 = [r for r in res if isExc(r)]
    print(f"{row['rank']:>2} {row['position']:6} {row['root'][:28]:28} keys {rule.keys}: exceptions {len(e0)}/{fq(e0):.0f} -> {len(e1)}/{fq(e1):.0f}; saving {sv(rule.results):.0f} -> {sv(res):.0f}", flush=True)
    tot["e0"] += len(e0); tot["e1"] += len(e1); tot["s0"] += sv(rule.results); tot["s1"] += sv(res)
print("multi-key rules total: exceptions", tot["e0"], "->", tot["e1"], "; saving", round(tot["s0"]), "->", round(tot["s1"]))
