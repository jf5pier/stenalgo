"""Trace why la/l'/une/un-prefix vanish from the selection (2026-10-03)."""
import sys
sys.path.insert(0, ".")
import scratch.select_expression_rules as sel
import src.expressionrules as er

T = {("la",), ("l'",), ("une",), ("un",), ("le",), ("les",)}

def wrapped(candidates, pool, budget=er.EXPR_RULE_BUDGET, **kw):
    for c in candidates:
        if c.kind == "attach" and c.units in T:
            print("CAND", c.units, c.position, "fam=", c.family, f"freq={c.freq:.3e}")
    orig = er.pruneRedundantVariants
    def pr(selected, pool, savingAt=er.proxySaving):
        before = list(selected)
        after = orig(selected, pool, savingAt)
        print("PRE-PRUNE", [(r.units, r.position, r.family, r.forms) for r in before if r.family and r.kind == "attach" and r.units in T])
        print("PRUNED", [(r.units, r.position) for r in before if r not in after and r.units in T])
        return after
    er.pruneRedundantVariants = pr
    res = er.selectExpressionRules(candidates, pool, budget=budget, **kw)
    print("SKIPS", res.skips)
    sys.exit(0)

sel.selectExpressionRules = wrapped
sel.main()
