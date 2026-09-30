"""Apply scratch/review-decisions.txt rulings to resources/spellingVariants.tsv.

Row numbers refer to the review rows in file order (scratch/review-batches.txt).
Plain 'active' flips status only. 'canonical override' rows also move the
canonical spelling and rewrite both drop columns to the other members.
"""
import csv, re, sys

OVERRIDES = {
    4: "allègement", 11: None, 18: "beluga", 31: "bouloter", 43: "carre",
    48: "chargeüre", 49: "charriotée", 66: "corole", 69: "curriculums",
    72: "dessouler", 76: "dissout", 81: "empiètement", 91: "gaillèterie",
    96: "garroter", 103: "griffon", 106: "grole", 113: "imprésario",
    129: "mangeoter", 131: "mariole", 145: "oignon", 146: "oignonière",
    156: "phylloxéra", 160: "plingeüre", 175: "soul", 176: "soulard",
    177: "souler", 178: "soulerie", 187: "sottie", 197: "tempos",
    204: "téocalli", 205: "vélum", 208: "égrugeüre",
}

decisions = {}
for line in open("scratch/review-decisions.txt"):
    if line.startswith("#") or not line.strip():
        continue
    parts = line.rstrip("\n").split("\t")
    n = int(parts[0])
    decisions[n] = parts[1]
assert len(decisions) == 209, len(decisions)

with open("resources/spellingVariants.tsv", newline="", encoding="utf-8") as f:
    lines = [l.rstrip("\n") for l in f if not l.startswith("#")]
rows = list(csv.DictReader(lines, delimiter="\t"))
fieldnames = list(rows[0].keys())

review_idx = 0
changed = 0
for row in rows:
    if row["status"] != "review":
        continue
    review_idx += 1
    dec = decisions[review_idx]
    row["status"] = dec
    canon = OVERRIDES.get(review_idx)
    if canon is not None:
        members = []
        for cell in (row["dropLemmes"], row["dropOrthos"], row["canonical"]):
            for m in cell.split():
                if m not in members:
                    members.append(m)
        # external canonicals: griffon (103) already a lexicon entry;
        # soulard/souler/soulerie (176-178) arrive via the reform1990 rewrite
        EXTERNAL = {103, 176, 177, 178}
        assert canon in members or canon == row["canonical"] or review_idx in EXTERNAL, (review_idx, canon, members)
        drops = [m for m in members if m != canon]
        row["canonical"] = canon
        row["dropLemmes"] = " ".join(drops)
        row["dropOrthos"] = " ".join(drops)
    if not row["note"].endswith("]") and row["note"]:
        row["note"] += " -- user ruling 2026-09-25"
    changed += 1
assert review_idx == 209, review_idx

# safety: no active canonical may appear in any active drop set
drops = set()
for row in rows:
    if row["status"] == "active":
        drops.update(row["dropLemmes"].split())
        drops.update(row["dropOrthos"].split())
conflicts = [(r["setId"], r["canonical"]) for r in rows
             if r["status"] == "active" and r["canonical"] in drops]
assert not conflicts, conflicts

header = [l for l in open("resources/spellingVariants.tsv", encoding="utf-8")
          if l.startswith("#")]
with open("resources/spellingVariants.tsv", "w", encoding="utf-8") as f:
    f.writelines(header)
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"applied {changed} rulings; "
      f"active={sum(r['status']=='active' for r in rows)}, "
      f"veto={sum(r['status']=='veto' for r in rows)}, "
      f"review={sum(r['status']=='review' for r in rows)}")
