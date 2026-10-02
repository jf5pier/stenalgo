"""Check that the FORM_COST prune in _greedyForms changes no rule, and time both versions."""
import pickle
import time

import src.affixrules as R

pool = pickle.load(open("scratch/affix-pool.pickle", "rb"))
idx = R.childrenIndex(pool)
anchors = sorted((k for k, c in pool.items() if c.isAnchor), key=lambda k: -pool[k].freq)
sample = anchors[:8] + anchors[1000:1015] + anchors[2500:2515]


def oldGreedy(root, remaining):
    forms = [root]
    remaining = list(remaining)
    bestScore = R.proxyScore(root.position, forms)
    while remaining and len(forms) < R.MAX_RULE_FORMS:
        best = None
        for cand in remaining:
            s = R.proxyScore(root.position, forms + [cand])
            if best is None or s > best[0]:
                best = (s, cand)
        s, cand = best
        if s <= bestScore:
            break
        forms.append(cand)
        remaining.remove(cand)
        bestScore = s
    return [R.candidateKey(f) for f in forms]


for name, alpha, excl, form in (("L", 1.0, 5.0, 10.0), ("H", 2.0, 150.0, 300.0)):
    R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = alpha, excl, form
    t = time.time()
    new = [[R.candidateKey(f) for f in R.buildCandidateRule(pool[k], idx).forms] for k in sample]
    tn = time.time() - t
    t = time.time()
    old = [oldGreedy(pool[k], R.descendantsOf(pool[k], idx)) for k in sample]
    to = time.time() - t
    print(name, "identical:", new == old, f"new {tn:.1f}s old {to:.1f}s", flush=True)
