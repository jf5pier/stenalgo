import csv

CARRIERS = {  # setId -> carrying lemme to clear from dropLemmes
    "impresario": "impresario", "media": "media", "phylloxera": "phylloxera",
    "sotie": "sotie", "velum": "velum",
}
lines = [l.rstrip("\n") for l in open("resources/spellingVariants.tsv", encoding="utf-8")
         if not l.startswith("#")]
rows = list(csv.DictReader(lines, delimiter="\t"))
fieldnames = list(rows[0].keys())
for row in rows:
    if row["setId"] in CARRIERS and row["status"] == "active":
        carrier = CARRIERS[row["setId"]]
        assert carrier in row["dropLemmes"].split(), row
        row["dropLemmes"] = " ".join(m for m in row["dropLemmes"].split() if m != carrier)
        print(f"cleared {carrier!r} from dropLemmes of {row['setId']} "
              f"(canonical {row['canonical']!r} rides on it)")
header = [l for l in open("resources/spellingVariants.tsv", encoding="utf-8") if l.startswith("#")]
with open("resources/spellingVariants.tsv", "w", encoding="utf-8") as f:
    f.writelines(header)
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(rows)
