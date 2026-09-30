"""For every ACTIVE variant set, check it against current LexiqueMixte.tsv.

Reports:
  CARRIER  -- dropLemmes contains the lemme that carries the canonical rows
  CANON-MISSING -- canonical has no rows in Mixte (set is inert or lethal)
"""
import csv, collections

rows = [l.rstrip("\n") for l in open("resources/spellingVariants.tsv", encoding="utf-8")
        if not l.startswith("#")]
sets = [r for r in csv.DictReader(rows, delimiter="\t") if r["status"] == "active"]

mixte = list(csv.DictReader(open("resources/LexiqueMixte.tsv", encoding="utf-8"),
                            delimiter="\t"))
by_ortho_lemme = collections.Counter((m["ortho"], m["lemme"]) for m in mixte)
lemmes_of = collections.defaultdict(set)
for m in mixte:
    lemmes_of[m["ortho"]].add(m["lemme"])

carrier = missing = stale = 0
for s in sets:
    canon = s["canonical"]
    dropL = set(s["dropLemmes"].split())
    dropO = set(s["dropOrthos"].split())
    canonLemmes = lemmes_of.get(canon, set())
    bad = dropL & canonLemmes
    if bad:
        carrier += 1
        print(f"CARRIER {s['setId']}: canonical {canon!r} rides on lemme(s) {sorted(bad)} "
              f"which are in dropLemmes")
    if not canonLemmes:
        missing += 1
        hits = sum(1 for m in mixte if m["ortho"] in dropO or m["lemme"] in dropL)
        print(f"CANON-MISSING {s['setId']}: canonical {canon!r} has no Mixte rows"
              + (f" ({hits} drop rows present)" if hits else " (set fully inert)"))
print(f"\n{len(sets)} active sets: {carrier} carrier conflicts, {missing} canonical-missing")
