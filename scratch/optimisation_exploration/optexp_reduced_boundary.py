"""C4, boundary risk of the reduced outlines: a reduced outline R (text, strokes joined by '/') is risky when
  (a) some live multi-stroke outline is R/Y or X/R with the rest (Y or X) live: typing the word then the neighbour is swallowed by the longer entry, or
  (b) R itself splits into >= 2 live outlines (only for multi-stroke R).
'live' = the shipped dictionary, affix dictionary and brief dictionary plus every reduced outline of the file (same measure as src/briefs.py BoundaryRisk).
The baseline is the same count for the existing live outlines of the shipped dictionary (the risk theory already carries).
Usage: python scratch/optimisation_exploration/optexp_reduced_boundary.py out/reduced_outlines_best4.tsv"""
import csv
import json
import sys
from collections import Counter

FILES = ("plover_stenalgo_dictionary.json", "plover_stenalgo_affix_dictionary.json", "plover_stenalgo_brief_dictionary.json")


def split(live: set[str], o: str) -> bool:
    s = tuple(o.split("/"))
    n = len(s)
    reach = [False] * (n + 1)
    reach[0] = True
    for j in range(1, n + 1):
        for i in range(j):
            if reach[i] and not (i == 0 and j == n) and "/".join(s[i:j]) in live:
                reach[j] = True
                break
    return reach[n]


def main() -> None:
    names: dict[str, str] = {}
    live: set[str] = set()
    for p in FILES:
        for k, v in json.load(open(p, encoding="utf8")).items():
            live.add(k)
            names.setdefault(k, v)
    base = set(live)
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf8"), delimiter="\t"))
    reduced = {r["short"]: r["spelling"] for r in rows}
    live |= set(reduced)
    swallow: dict[str, list[str]] = {}     # stroke-run -> the live multi-stroke outlines that start / end with it
    for L in live:
        s = L.split("/")
        for i in range(1, len(s)):
            head, tail = "/".join(s[:i]), "/".join(s[i:])
            if head in live and tail in live:
                swallow.setdefault(head, []).append(L)
                swallow.setdefault(tail, []).append(L)
    risky = {r: ws for r in reduced if (ws := swallow.get(r))}
    split_risky = {r for r in reduced if "/" in r and split(live, r)}
    print(f"{len(reduced)} reduced outlines; live outlines {len(live)}")
    print(f"(a) swallowed/swallowing: {len(risky)} ({100 * len(risky) / len(reduced):.2f}%); (b) multi-stroke and splittable: {len(split_risky)}")
    # baseline: the share of the shipped dictionary's single-stroke outlines that take part in a swallowing pair
    bs = {}
    for L in base:
        s = L.split("/")
        for i in range(1, len(s)):
            head, tail = "/".join(s[:i]), "/".join(s[i:])
            if head in base and tail in base:
                bs[head] = bs[tail] = 1
    singles = [k for k in base if "/" not in k]
    print(f"baseline: {sum(1 for k in singles if k in bs)} of {len(singles)} shipped single-stroke outlines "
          f"({100 * sum(1 for k in singles if k in bs) / len(singles):.2f}%) are in a swallowing pair")
    cnt = Counter(len(r.split("/")) for r in risky)
    print("risky by stroke count:", dict(cnt))
    for r in sorted(risky)[:15]:
        print("  ", r, reduced[r], "->", [(L, names.get(L) or reduced.get(L)) for L in risky[r][:2]])


if __name__ == "__main__":
    main()
