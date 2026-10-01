import pickle, csv
from src import affixrules as R
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = 2.0, 150.0, 300.0
ruleCache = {}
anchors, _dec = R.resolveVariantRivals(cands, pk, ctx, keypresses, ruleCache)
rows = list(csv.DictReader(open("scratch/affix-sweep/H/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
byExcFreq = sorted(rows, key=lambda r: -float(r["exceptionFreq"]))
removed = {(r["position"], r["root"]) for r in byExcFreq[:4]}
print("removing:", removed, flush=True)
def run(label, drop, budget):
    keep = [k for k in anchors if (k[0], k[3]) not in drop]
    res = R.selectRules(cands, pk, ctx, keypresses, budget=budget, curveLength=40, anchors=keep, ruleCache=dict(ruleCache))
    res = R.swapPass(res)
    sel = res.selected
    w = sum(r.wordExceptions for r in sel); f = sum(r.exceptionFreq for r in sel)
    print(f"{label}: {len(sel)} rules, exceptions {w} words / {f:.0f} freq, credited saving {res.curve[len(sel)-1]:.0f} (curve end {res.curve[-1]:.0f})", flush=True)
    return sel
base = run("H baseline (30)", set(), 30)
refill = run("H without top-4 exception rules, refilled to 30", removed, 30)
short = run("H without top-4 exception rules, 26 rules", removed, 26)
b = {(r.position, r.root.ortho) for r in base}
for label, s in (("refill", refill), ("26", short)):
    cur = {(r.position, r.root.ortho) for r in s}
    print(label, "new rules:", [(p, o[:30], r.wordExceptions, round(r.exceptionFreq, 1)) for r in s for p, o in [(r.position, r.root.ortho)] if (p, o) not in b])
    print(label, "dropped vs baseline:", [(p, o[:30]) for p, o in b - cur])
