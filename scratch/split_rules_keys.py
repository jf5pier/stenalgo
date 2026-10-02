"""Can the exceptions of the big H rules be explained by the stem's first phoneme, and does a
second key for those stems reduce exceptions?"""
import csv, pickle, collections, itertools
from src import affixrules as R
from src.affixes import Binding, RULE, poolCarriers, PREFIX
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(cands, records, starboard)
idx = R.childrenIndex(cands)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = 2.0, 150.0, 300.0
byOrtho = {}
for k, c in cands.items():
    if c.isAnchor and c.k == 1:
        byOrtho.setdefault((c.position, c.ortho), []).append(k)
rows = list(csv.DictReader(open("scratch/affix-sweep/H/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
targets = sorted(rows, key=lambda r: -int(r["wordExceptions"]))[:5]

POS = "prefix"
def neighbourKeys(c):
    base = c.rec.base
    ni = c.start + c.span if POS == "prefix" else c.start - 1
    return frozenset(base[ni]) if 0 <= ni < len(base) else frozenset()
def part(k): return ctx._partOf.get(k, "?")[:1]

def evalKey(rule, carriers, k):
    (res,) = R.simulate([(Binding(rule.position, RULE, k), carriers)], ctx, boundaryRisk=False)
    return res

def bestKeyFor(rule, carriers):
    """Best legal key for this carrier subset under the same admissibility as chooseRuleKeypress."""
    excl = R.exclusionCountOf(rule.forms)
    groups = R._neighbourGroups(rule.position, carriers)
    best = None
    for k in keypresses:
        if R._exceptionRateFloor(groups, k, ctx) > R.MAX_EXCEPTION_RATE:
            continue
        res = evalKey(rule, carriers, k)
        sc = R.ruleScoreFromResults(res, excl, 1)[0]
        if sc > 0 and R._exceptionRate(res) <= R.MAX_EXCEPTION_RATE and (best is None or sc > best[0]):
            best = (sc, k, res)
    return best

fq = lambda rs: sum(r.carrier.rec.frequency for r in rs)
for row in targets:
    rule = None
    for key in byOrtho[(row["position"], row["root"])]:
        r = R.buildCandidateRule(cands[key], idx); R.chooseRuleKeypress(r, pk, ctx, keypresses)
        if len(r.results) == int(row["carriers"]) and r.wordExceptions == int(row["wordExceptions"]):
            rule = r; break
    if rule is None:
        print("NO MATCH", row["root"]); continue
    isExc = lambda r: r.gain <= 0 and r.reason in R.WORD_EXCEPTION_REASONS
    exc = [r for r in rule.results if isExc(r)]
    print(f"\n=== {row['position']} `{row['root'][:40]}` key {rule.keys}: {len(rule.results)} words, exceptions {len(exc)} words / {fq(exc):.0f} freq; "
          f"reasons {dict(collections.Counter(r.reason for r in exc))}", flush=True)
    POS = row["position"]
    tot, ex = collections.Counter(), collections.Counter()
    exf = collections.Counter()
    clash = [r for r in exc if set(neighbourKeys(r.carrier)) & set(rule.keys)]
    print(f"  exceptions whose next stroke already contains the rule key {rule.keys}: {len(clash)} of {len(exc)} words, "
          f"{fq(clash):.0f} of {fq(exc):.0f} freq")
    for r in rule.results:
        for p in neighbourKeys(r.carrier):
            tot[p] += 1
            if isExc(r): ex[p] += 1; exf[p] += r.carrier.rec.frequency
    print("  exceptions by key present in the stem's first stroke (key id/part: exc words/all words with the key, exc freq):")
    for p, n in ex.most_common(8):
        print(f"    key {p}/{part(p)} {n}/{tot[p]} ({n/tot[p]:.0%}) freq {exf[p]:.0f}")
    # greedy split: add phonemes (from the top exception phonemes) to a class B that gets its own key
    carriers = poolCarriers(rule.forms)
    cand = [p for p, _ in ex.most_common(8)]
    chosen = []
    for step in range(4):
        bestOpt = None
        for p in cand:
            if p in chosen: continue
            cls = chosen + [p]
            B = [c for c in carriers if (neighbourKeys(c) & set(cls))]; A = [c for c in carriers if not (neighbourKeys(c) & set(cls))]
            if not B or not A: continue
            kb = bestKeyFor(rule, B)
            if kb is None: continue
            resA = evalKey(rule, A, rule.keys)
            resB = kb[2]
            e = [r for r in resA + resB if isExc(r)]
            saved = sum(r.carrier.rec.frequency * r.gain for r in resA + resB if r.gain > 0)
            opt = (fq(e), len(e), saved, cls, kb[1])
            if bestOpt is None or opt[0] < bestOpt[0]: bestOpt = opt
        if bestOpt is None: break
        chosen = bestOpt[3]
        base = sum(r.carrier.rec.frequency * r.gain for r in rule.results if r.gain > 0)
        print(f"  split off stems whose first stroke has key(s) {chosen} -> key B {bestOpt[4]}: exceptions {bestOpt[1]} words / {bestOpt[0]:.0f} freq "
              f"(was {len(exc)} / {fq(exc):.0f}); stroke saving {bestOpt[2]:.0f} (was {base:.0f})", flush=True)
