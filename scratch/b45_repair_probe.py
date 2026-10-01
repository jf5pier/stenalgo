import collections, csv
from src.verbparadigm import spliceParticiplePhon
from scratch.b45_backtest import rows, word
stats = collections.Counter(); ex = collections.defaultdict(list)
with open("resources/LexiqueSynthetic.tsv", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
        if "par:pas" not in r["infover"]: continue
        stats["rows"] += 1
        slots = rows.get(r["lemme"], {})
        key = (r["genre"], r["nombre"])
        if key in slots and slots[key]["ortho"] == r["ortho"]:
            stats["dup"] += 1; ex["dup"].append((r["ortho"], r["phon"], slots[key]["phon"])); continue
        if not slots: stats["nodonor"] += 1; ex["nodonor"].append(r["ortho"]); continue
        donor = next((d for (g, _), d in slots.items() if g == r["genre"]), next(iter(slots.values())))
        phon, syll = spliceParticiplePhon(word(donor), r["genre"], r["ortho"])
        cat = "same" if (phon, syll) == (r["phon"], r["syll_cv"]) else ("phon" if phon != r["phon"] else "syll")
        stats[cat] += 1; ex[cat].append((r["ortho"], r["genre"], r["phon"], r["syll_cv"], "->", phon, syll, "donor", donor["ortho"]))
print(stats)
for k, v in ex.items():
    print(k, len(v)); [print("  ", *e) for e in v[:60]]
