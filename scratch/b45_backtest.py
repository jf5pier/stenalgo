"""B45 backtest: splice each attested participle into every other attested
gender/number slot of its lemma; compare phon with the old verbatim rule."""
import collections, csv
from src.verbparadigm import spliceParticiplePhon
from src.word import GramCat, Word

rows = collections.defaultdict(dict)
with open("resources/LexiqueMixte.tsv", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["cgram"] == "VER" and "par:pas" in r["infover"] and r["genre"] in "mf" and r["nombre"] in "sp" and r["genre"] and r["nombre"]:
            rows[r["lemme"]].setdefault((r["genre"], r["nombre"]), r)

def word(r):
    return Word(ortho=r["ortho"], phonology=r["phon"], lemme=r["lemme"], gramCat=GramCat.VER,
                orthoGramCat=[GramCat.VER], gender=r["genre"], number=r["nombre"], infoVerb="par:pas;",
                rawSyllCV=r["syll_cv"], rawOrthosyllCV=r["orthosyll_cv"], frequencyBook=0.0, frequencyFilm=0.0)

stats = collections.Counter(); bad = []
for lemme, slots in rows.items():
    for (dg, dn), donor in slots.items():
        for (tg, tn), target in slots.items():
            if (dg, dn) == (tg, tn) or dg == tg:
                continue
            old = donor["phon"]
            try:
                new, _ = spliceParticiplePhon(word(donor), tg, target["ortho"])
            except ValueError as e:
                stats["error"] += 1; bad.append(("ERR", lemme, donor["ortho"], target["ortho"], str(e))); continue
            stats["pairs"] += 1
            stats["old_ok"] += old == target["phon"]
            stats["new_ok"] += new == target["phon"]
            if new != target["phon"] and old == target["phon"]:
                bad.append(("REGRESS", lemme, donor["ortho"], donor["phon"], target["ortho"], target["phon"], new))
print(stats)
for b in bad[:40]: print(*b)
print(len(bad))
