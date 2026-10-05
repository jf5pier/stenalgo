"""Print the review's proposals for every pending item, without asking or writing anything."""
import sys
from util import review_affix_rules as V
from util.build_affix_rules import Pending, loadStore
from src.affixdecisions import loadDecisions
store = loadStore("AffixSelection.pickle")
items = [Pending(**d) for d in store["selection"]["pending"]]
propose = V._realProposer("affix_decisions.json", store["selection"]["rules"])
d = loadDecisions()
for it in items:
    print(f"\n=== {it.line()}", flush=True)
    p = propose(it, d)
    if p is None: print("  (no proposal)"); continue
    V._show(p, print)
