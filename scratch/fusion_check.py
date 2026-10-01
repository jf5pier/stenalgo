"""For every UNAPPROVED fusion (variant merge) that contains an approved anchor: score
(1) the approved rules alone and (2) the fused anchor with exactly the approved parts' scoped forms
(the unapproved spellings anchor-only). Setting D, flag on. Output scratch/fusion-check-2026-10-01.md"""
import pickle, sys, time
sys.path.insert(0, ".")
from src import affixes as A, affixrules as R
from src.affixscopes import SCOPES
from util import affix_scan as S

A.RULE_PARTIAL_OVERLAP = True
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == "D")
starboard = S.loadStarboard()
records = S.loadRecords(starboard, False)
pool = pickle.load(open("scratch/affix-pool.pickle", "rb"))
ctx, pk, keypresses, lemmas = S._engine(pool, records, starboard)
key = lambda c: (c.position, c.ortho, c.phono)
byKey = {(c.position, c.k, c.phono, c.ortho): c for c in pool.values()}
idx = R.childrenIndex(pool)

def evaluate(rule):
    R.chooseRuleKeypress(rule, pk, ctx, keypresses)
    return rule

def line(rule):
    if rule.keys is None: return "no legal key"
    return f"{rule.score:.0f} (keys {rule.keys}, saved {rule.strokeFreqSaved:.0f}, exc {rule.wordExceptions}/{rule.exceptionFreq:.0f}, fb {rule.fallbacks})"

out = ["# Unapproved fusions that contain an approved anchor (setting D, flag on)", "",
       "alone = the approved rule(s) as decided; fused = merged anchor, approved scoped forms kept, other spellings anchor-only.", ""]
for m in sorted((c for c in pool.values() if c.isAnchor and c.mergeParts and key(c) not in SCOPES), key=lambda c: -c.freq):
    parts = [byKey[k] for k in m.mergeParts if k in byKey]
    ap = [x for x in parts if key(x) in SCOPES]
    if not ap: continue
    un = [x for x in parts if key(x) not in SCOPES]
    t = time.time()
    alone = [evaluate(R.buildCandidateRule(x, idx)) for x in ap]
    forms = [m] + [c for x in ap for c in R.descendantsOf(x, idx) if c.isScoped]
    fused = evaluate(R.Rule(m.position, m, forms, score=0.0))
    apIdx = {c.rec.idx for x in ap for c in x.carriers}
    added = sorted((c for c in m.carriers if c.rec.idx not in apIdx), key=lambda c: -c.rec.frequency)
    sa = sum(r.score for r in alone)
    out += [f"## {m.position} `{m.ortho}` /{m.phono}/", "",
            f"- approved parts: {', '.join(f'`{x.ortho}`' for x in ap)}; unapproved spellings: {', '.join(f'`{x.ortho}`({len(x.carriers)})' for x in un) or 'none'}",
            f"- words added by the unapproved spellings: {len(added)} (freq {sum(c.rec.frequency for c in added):.0f}); top: {', '.join(c.rec.ortho for c in added[:8])}"]
    for r in alone: out.append(f"- ALONE `{r.root.ortho}`: {line(r)}")
    out += [f"- FUSED: {line(fused)}; forms {len(fused.forms) - 1}",
            f"- fused - alone(sum) = {fused.score - sa:+.0f}" + (" (fusion also frees a key)" if len(ap) == 1 else f" (merges {len(ap)} approved rules onto one key)"), ""]
    print(f"{m.ortho[:30]:30} alone {sa:.0f} fused {fused.score:.0f} d {fused.score - sa:+.0f} added {len(added)} ({time.time() - t:.0f}s)", flush=True)
open("scratch/fusion-check-2026-10-01.md", "w").write("\n".join(out) + "\n")
