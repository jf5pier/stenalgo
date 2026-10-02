"""Render a sweep's affix-rules.tsv as a markdown table: one line per rule, full form expansion."""
import csv, sys
path = sys.argv[1] if len(sys.argv) > 1 else "scratch/affix-sweep-partial/H/affix-rules.tsv"
out = sys.argv[2] if len(sys.argv) > 2 else None
rows = list(csv.DictReader(open(path), delimiter="\t"))
L = ["| # | pos | anchor | keys | forms (full expansion) | words | stroke-freq saved | exc words | exc freq |",
     "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['rank']} | {r['position']} | `{r['root']}` | {r['keys']} | {r['forms'].replace('|', '\\|')} | "
             f"{r['carriers']} | {float(r['strokeFreqSaved']):.0f} | {r['wordExceptions']} | {float(r['exceptionFreq']):.1f} |")
txt = "\n".join(L) + "\n"
if out: open(out, "w").write(txt)
print(txt)
