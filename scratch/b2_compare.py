"""B2 before/after: phonetic theory stroke counts and Plover dictionary changes."""
import csv, json, collections, sys
def theory(path):
    byWord = collections.defaultdict(set)
    for r in csv.DictReader(open(path), delimiter="\t"):
        for w in r["words"].split(","):
            byWord[w].add(r["strokes"])
    return byWord
b, a = theory("scratch/b2r2-before/phonetic_theory.tsv"), theory("phonetic_theory.tsv")
changed = [w for w in b.keys() & a.keys() if b[w] != a[w]]
fewer = [w for w in changed if min(s.count("/") for s in a[w]) < min(s.count("/") for s in b[w])]
more = [w for w in changed if min(s.count("/") for s in a[w]) > min(s.count("/") for s in b[w])]
print(f"phonetic theory: spellings {len(b)} -> {len(a)}; stroke set changed {len(changed)}; "
      f"shortest entry shorter {len(fewer)}, longer {len(more)}; gone {len(b.keys()-a.keys())}, new {len(a.keys()-b.keys())}")
print("  gone:", sorted(b.keys()-a.keys())[:30]); print("  new:", sorted(a.keys()-b.keys())[:30])
print("  longer:", sorted(more)[:30])
pb, pa = json.load(open("scratch/b2r2-before/plover_stenalgo_dictionary.json")), json.load(open("plover_stenalgo_dictionary.json"))
sb, sa = set(pb.values()), set(pa.values())
print(f"plover: entries {len(pb)} -> {len(pa)}; removed {len(pb.keys()-pa.keys())}, added {len(pa.keys()-pb.keys())}, "
      f"re-pointed {sum(pb[k]!=pa[k] for k in pb.keys()&pa.keys())}; spellings {len(sb)} -> {len(sa)} "
      f"(lost {len(sb-sa)}, gained {len(sa-sb)})")
print("  spellings lost:", sorted(sb-sa)[:40]); print("  spellings gained:", sorted(sa-sb)[:40])
for w in ["cannes", "abonne", "dénie", "porte", "attendez", "achètera", "fricote"]:
    print(f"  {w}: before {sorted(k for k,v in pb.items() if v==w)} after {sorted(k for k,v in pa.items() if v==w)}")
