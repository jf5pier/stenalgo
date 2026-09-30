"""Cross-check: which A7-pooled nodes are selected-rule roots in the last full run,
of those which have a lattice-grown same-signature twin (the orphan disease),
and how many of the 187 conflicts are linkable (tail node present in the pool).
Fast (~10 s, cached records). Measurement only.
"""
import csv

from src import affixes as A
from util.affix_scan import loadStarboard, loadRecords

sb = loadStarboard()
recs = loadRecords(sb, False)
seedPairs, _ = A.loadSeeds()
pool = A.buildCandidates(recs, seedPairs, legacy=False)


def a7Sig(c):
    if c.grownFromKey is not None or c.rootKey is not None or c.k < 2:
        return None
    if not c.isGeneralized or c.slots:
        return None
    syls = c.phono.split(".")
    if c.position == A.SUFFIX:
        return (c.position, c.k, ".".join(syls[1:]), "onset", syls[0])
    return (c.position, c.k, ".".join(syls[:-1]), "onset", syls[-1])


def grownSig(c):
    if c.grownFromKey is None or len(c.slots) != 1 or c.slots[0].kind != "onset":
        return None
    return (c.position, c.k, c.grownFromKey[2], "onset", c.slots[0].value)


a7sigs = {}
grownSigs = set()
for c in pool.values():
    s = a7Sig(c)
    if s:
        a7sigs[s] = c
    s = grownSig(c)
    if s:
        grownSigs.add(s)

byPosKPhono: dict = {}
for key, c in pool.items():
    byPosKPhono.setdefault((c.position, c.k, c.phono), []).append(c)


def tailNode(c, tail):
    return byPosKPhono.get((c.position, c.k - 1, tail))


conflict = {s: c for s, c in a7sigs.items() if s in grownSigs}
print(f"A7 nodes (k>=2, sig): {len(a7sigs)}; with grown twin: {len(conflict)}; "
      f"without: {len(a7sigs) - len(conflict)}")
linkable = sum(1 for s, c in conflict.items() if tailNode(c, s[2]))
print(f"linkable (tail node present in pool): {linkable} / {len(conflict)}")
nolink = [(s, c) for s, c in conflict.items() if not tailNode(c, s[2])]
print("not linkable (tail pruned -- would stay roots):")
for s, c in sorted(nolink, key=lambda t: -t[1].freq):
    print(f"  {c.position[:4]} k={c.k} tail={s[2]!r} rest={s[4]!r}  {c.ortho!r} |{len(c.carriers)}| f={c.freq:.0f}")

# selected roots from the last full run
roots = {}
with open("scratch/affix-rules.tsv", encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        roots[row["root"]] = (row["rank"], row["score"], row["forms"])
print(f"\nselected roots: {len(roots)}")
diseased = []
for s, c in conflict.items():
    if c.ortho in roots:
        rank, score, forms = roots[c.ortho]
        tailL = tailNode(c, s[2])
        tail = tailL[0] if tailL else None
        tailSel = tail is not None and tail.ortho in roots
        diseased.append((rank, c.ortho, score, s, tailSel, tail.ortho if tail else None,
                         roots.get(tail.ortho, ("?", "?"))[0] if tailSel else "-"))
print(f"\nA7-conflict nodes that ARE selected roots (orphan-disease candidates):")
for rank, ortho, score, s, tailSel, tailO, tailRank in sorted(diseased):
    print(f"  rank {rank}: root {ortho!r} (score {score}) tail={s[2]!r} -> tail rule selected: "
          f"{tailSel} (root {tailO!r}, rank {tailRank})")
print(f"\nALL selected A7 roots, with twin status:")
for ortho, (rank, score, _f) in sorted(roots.items(), key=lambda t: int(t[1][0])):
    c = next((x for x in a7sigs.values() if x.ortho == ortho), None)
    if c is None:
        continue
    hasTwin = a7Sig(c) in conflict
    tailL = tailNode(c, a7Sig(c)[2])
    tail = tailL[0] if tailL else None
    tailSel = tail is not None and tail.ortho in roots
    tailOrtho = tail.ortho if tail is not None else "(absent)"
    print(f"  rank {rank}: {ortho!r} (score {score}) twin={'YES' if hasTwin else 'no'} "
          f"tail={tailOrtho!r} tailSelected={tailSel}")
