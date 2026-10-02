"""Spot-checks after the spelling-variant rebuild (S1 output onwards)."""
import csv, sys
from src.spellingvariants import loadSpellingVariantDrops

drops = loadSpellingVariantDrops()

def rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

mixte = rows("resources/LexiqueMixte.tsv")
orthos = {m["ortho"] for m in mixte}
lemmes = {m["lemme"] for m in mixte}

fail = 0
def check(cond, msg):
    global fail
    print(("OK  " if cond else "FAIL") + " " + msg)
    if not cond:
        fail += 1

# 1. no dropped spelling survives anywhere
leaked = (orthos & drops.dropOrthos) | (lemmes & drops.dropLemmes)
check(not leaked, f"no dropped spelling in Mixte (leaked: {sorted(leaked)[:10]})")

# 2. key user rulings
for present in ["oignon", "événement", "beluga", "carre", "dessouler",
                "soul", "souler", "soulard", "soulerie", "balle", "mari",
                "par", "abattage", "âge", "sottie", "imprésario", "vélum"]:
    check(present in orthos, f"canonical present: {present}")
for absent in ["ognon", "évènement", "béluga", "care", "dessaouler", "saoul",
               "saouler", "soûler", "saoulard", "saoulerie", "bale", "mary",
               "abatage", "appas", "trimbaler", "zyeuter", "maffia"]:
    check(absent not in orthos, f"variant gone: {absent}")

# 3. vetoes untouched
for kept in ["tâche", "tache", "sur", "sûr", "gale", "galle", "colon", "côlon",
             "fût", "fut", "forêt", "foret"]:
    check(kept in orthos, f"veto/exception kept: {kept}")

print(f"\n{'FAILURES: ' + str(fail) if fail else 'all checks passed'} "
      f"({len(mixte)} Mixte rows)")
sys.exit(1 if fail else 0)
