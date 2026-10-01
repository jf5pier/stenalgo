import csv
S = ("L", "M", "H")
data = {}
for s in S:
    rows = list(csv.DictReader(open(f"scratch/affix-sweep/{s}/affix-rules.tsv", encoding="utf-8"), delimiter="\t"))
    data[s] = rows
# union-find on (position, root variants)
parent = {}
def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b): parent[find(a)] = find(b)
for s in S:
    for r in data[s]:
        vs = [(r["position"], v) for v in r["root"].split("|")]
        for v in vs[1:]: union(vs[0], v)
fam = {}
for s in S:
    for r in data[s]:
        f = find((r["position"], r["root"].split("|")[0]))
        fam.setdefault(f, {})[s] = r
def cell(r):
    nf = r["forms"].count(" | ") + 1
    return f"#{r['rank']} · {nf}f · exc {r['wordExceptions']} ({float(r['exceptionFreq']):.0f}) · {r['carriers']}w"
order = sorted(fam.items(), key=lambda kv: min(int(r["rank"]) for r in kv[1].values()))
L = ["# L / M / H per-rule comparison (2026-09-29, fixed lexicon)", "",
     "Cell = rank · number of forms (f) · word exceptions (their frequency) · carrier words (w). `—` = not selected.", "",
     "| rule | in | L | M | H |", "|---|---|---|---|---|"]
for (pos, root), m in order:
    label = next(iter(m.values()))["root"]
    label = label if len(label) <= 40 else label[:37] + "..."
    L.append(f"| {pos} `{label}` | {''.join(s for s in S if s in m)} | " + " | ".join(cell(m[s]) if s in m else "—" for s in S) + " |")
L += ["", "## Totals", "", "| | rules | forms | word exceptions | exception freq | carrier words | strokeFreqSaved | score |", "|---|---|---|---|---|---|---|---|"]
for s in S:
    rs = data[s]
    L.append(f"| {s} | {len(rs)} | {sum(r['forms'].count(' | ') + 1 for r in rs)} | {sum(int(r['wordExceptions']) for r in rs)} | "
             f"{sum(float(r['exceptionFreq']) for r in rs):.0f} | {sum(int(r['carriers']) for r in rs)} | "
             f"{sum(float(r['strokeFreqSaved']) for r in rs):.0f} | {sum(float(r['score']) for r in rs):.0f} |")
inter = [k for k, m in fam.items() if len(m) == 3]
L += ["", f"In all three: {len(inter)} rules; only L: {sum(1 for m in fam.values() if set(m) == {'L'})}; "
      f"only M: {sum(1 for m in fam.values() if set(m) == {'M'})}; only H: {sum(1 for m in fam.values() if set(m) == {'H'})}; "
      f"L∩M: {sum(1 for m in fam.values() if {'L','M'} <= set(m))}; M∩H: {sum(1 for m in fam.values() if {'M','H'} <= set(m))}."]
L += ["", "## Worst exceptions per setting (rules with the most exception words)", ""]
for s in S:
    top = sorted(data[s], key=lambda r: -int(r["wordExceptions"]))[:5]
    L.append(f"- **{s}**: " + "; ".join(f"{r['position']} `{r['root'][:25]}` {r['wordExceptions']} ({r['topExceptions'].replace(',', ', ')[:60]})" for r in top))
open("scratch/affix-sweep/weights-comparison.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
